"""
文档相关 API 路由
"""
import os
import shutil
import base64
from datetime import datetime
from typing import Optional
from fastapi import APIRouter, UploadFile, File, Form, HTTPException, Query, Depends
from fastapi.responses import FileResponse
from pathlib import Path

from app.schemas.document import (
    DocumentCreate,
    DocumentUpdate,
    DocumentResponse,
    DocumentListResponse,
    UploadResponse,
    ParseResponse,
)
from app.models.document import storage
from app.api.folders import update_folder_timestamp
from app.services.mineru_service import mineru_service
from app.core.config import settings
from app.schemas.document import ParseStatus

router = APIRouter()


@router.post("/upload", response_model=UploadResponse)
async def upload_document(
    file: UploadFile = File(...),
    folderId: str = Form("root"),
):
    """
    上传文档

    支持的文件类型：PDF, DOCX, TXT
    """
    # 验证文件类型
    file_ext = Path(file.filename).suffix.lower().lstrip(".")
    if file_ext not in ["pdf", "docx", "txt"]:
        raise HTTPException(status_code=400, detail="不支持的文件类型")

    # 确保上传目录存在
    os.makedirs(settings.UPLOAD_DIR, exist_ok=True)

    # 生成文件路径
    file_id = f"{datetime.now().strftime('%Y%m%d%H%M%S')}_{file.filename}"
    file_path = os.path.join(settings.UPLOAD_DIR, file_id)

    # 保存文件
    try:
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"文件保存失败: {str(e)}")

    # 创建文档记录
    file_size = os.path.getsize(file_path)
    doc_data = DocumentCreate(
        title=Path(file.filename).stem,
        fileName=file.filename,
        fileType=file_ext,
        fileSize=file_size,
        tags=[],
        folderId=folderId,
    )

    doc = storage.create_document(doc_data, file_path)

    # 更新知识库时间戳
    update_folder_timestamp(folderId)

    return UploadResponse(
        documentId=doc["id"],
        fileName=doc["fileName"],
        fileSize=doc["fileSize"],
    )


@router.post("/{document_id}/parse")
async def parse_document(document_id: str):
    """
    启动文档解析（后台任务）

    返回任务ID，前端可以轮询任务状态
    """
    doc = storage.get_document(document_id)
    if not doc:
        raise HTTPException(status_code=404, detail="文档不存在")

    # 更新状态为解析中
    storage.update_parse_status(document_id, ParseStatus.PARSING)

    # 获取文件路径
    file_path = doc.get("filePath")
    if not file_path or not os.path.exists(file_path):
        storage.update_parse_status(
            document_id, ParseStatus.ERROR, error_message="文件不存在"
        )
        raise HTTPException(status_code=404, detail="文件不存在")

    # 提交后台任务
    task_id = f"parse_{document_id}"

    async def parse_task():
        """解析任务"""
        try:
            markdown_content, error_message, images = await mineru_service.parse_pdf(
                file_path, document_id
            )

            if error_message:
                storage.update_parse_status(
                    document_id, ParseStatus.ERROR, error_message=error_message
                )
            else:
                storage.update_parse_status(
                    document_id, ParseStatus.SUCCESS, markdown_content=markdown_content
                )
        except Exception as e:
            storage.update_parse_status(
                document_id, ParseStatus.ERROR, error_message=str(e)
            )

    # 提交到后台任务管理器
    from app.services.task_manager import task_manager
    await task_manager.submit_task(task_id, parse_task)

    return {
        "taskId": task_id,
        "message": "解析任务已提交，请稍后查询结果"
    }


@router.get("/{document_id}/parse/status")
async def get_parse_status(document_id: str):
    """
    获取解析任务状态
    """
    doc = storage.get_document(document_id)
    if not doc:
        raise HTTPException(status_code=404, detail="文档不存在")

    return {
        "documentId": document_id,
        "status": doc.get("parseStatus", "pending"),
        "parsed": doc.get("parsed", False)
    }


@router.get("", response_model=DocumentListResponse)
async def list_documents(
    folder: Optional[str] = Query(None, description="文件夹 ID"),
    tag: Optional[str] = Query(None, description="标签"),
    search: Optional[str] = Query(None, description="搜索关键词"),
    skip: int = Query(0, ge=0, description="跳过数量"),
    limit: int = Query(100, ge=1, le=1000, description="返回数量"),
):
    """
    获取文档列表
    """
    documents, total = storage.list_documents(
        folder=folder, tag=tag, search=search, skip=skip, limit=limit
    )

    return DocumentListResponse(documents=documents, total=total)


@router.get("/{document_id}", response_model=DocumentResponse)
async def get_document(document_id: str):
    """
    获取文档详情
    """
    doc = storage.get_document(document_id)
    if not doc:
        raise HTTPException(status_code=404, detail="文档不存在")

    return DocumentResponse(**doc)


@router.put("/{document_id}", response_model=DocumentResponse)
async def update_document(document_id: str, data: DocumentUpdate):
    """
    更新文档
    """
    doc = storage.update_document(document_id, data)
    if not doc:
        raise HTTPException(status_code=404, detail="文档不存在")

    # 更新知识库时间戳
    folder_id = doc.get("folderId", "root")
    update_folder_timestamp(folder_id)

    return DocumentResponse(**doc)


@router.put("/{document_id}/content", response_model=DocumentResponse)
async def update_document_content(
    document_id: str, data: dict
):
    """
    更新文档内容
    """
    markdown_content = data.get("markdownContent", "")
    doc = storage.update_document(
        document_id, DocumentUpdate(markdownContent=markdown_content)
    )
    if not doc:
        raise HTTPException(status_code=404, detail="文档不存在")

    # 更新知识库时间戳
    folder_id = doc.get("folderId", "root")
    update_folder_timestamp(folder_id)

    return DocumentResponse(**doc)


@router.delete("/{document_id}")
async def delete_document(document_id: str):
    """
    删除文档
    """
    # 先获取文档信息，以便更新文件夹时间戳
    doc = storage.get_document(document_id)
    if not doc:
        raise HTTPException(status_code=404, detail="文档不存在")

    folder_id = doc.get("folderId", "root")

    success = storage.delete_document(document_id)
    if not success:
        raise HTTPException(status_code=404, detail="文档不存在")

    # 更新知识库时间戳
    update_folder_timestamp(folder_id)

    return {"message": "删除成功"}


@router.get("/{document_id}/download")
async def download_document(
    document_id: str,
    format: str = Query("markdown", description="下载格式：pdf, markdown"),
    disposition: str = Query("attachment", description=" disposition：inline(预览) 或 attachment(下载)")
):
    """
    下载或预览文档
    """
    doc = storage.get_document(document_id)
    if not doc:
        raise HTTPException(status_code=404, detail="文档不存在")

    if format == "markdown":
        # 下载 Markdown 文件
        markdown_content = doc.get("markdownContent", "")
        if not markdown_content:
            raise HTTPException(status_code=400, detail="文档未解析或无内容")

        # 创建临时文件
        temp_file = f"/tmp/{doc['fileName']}.md"
        with open(temp_file, "w", encoding="utf-8") as f:
            f.write(markdown_content)

        return FileResponse(
            temp_file,
            media_type="text/markdown",
            filename=f"{doc['title']}.md",
        )

    elif format == "pdf":
        # 预览或下载原始 PDF 文件
        file_path = doc.get("filePath")
        if not file_path or not os.path.exists(file_path):
            raise HTTPException(status_code=404, detail="文件不存在")

        # 设置 Content-Disposition
        content_disposition = "inline" if disposition == "inline" else "attachment"

        # 对于inline预览，不设置filename以避免浏览器下载
        if disposition == "inline":
            return FileResponse(
                file_path,
                media_type="application/pdf",
                headers={"Content-Disposition": "inline"}
            )
        else:
            return FileResponse(
                file_path,
                media_type="application/pdf",
                filename=doc["fileName"]
            )

    else:
        raise HTTPException(status_code=400, detail="不支持的格式")


@router.get("/{document_id}/pdf-base64")
async def get_pdf_base64(document_id: str):
    """
    获取PDF的base64编码（用于前端渲染）
    """
    doc = storage.get_document(document_id)
    if not doc:
        raise HTTPException(status_code=404, detail="文档不存在")

    file_path = doc.get("filePath")
    if not file_path or not os.path.exists(file_path):
        raise HTTPException(status_code=404, detail="文件不存在")

    # 读取PDF文件并转换为base64
    with open(file_path, "rb") as f:
        pdf_data = f.read()

    base64_data = base64.b64encode(pdf_data).decode("utf-8")

    return {
        "base64": base64_data,
        "size": len(pdf_data)
    }


@router.get("/{document_id}/images/{image_name}")
async def get_document_image(document_id: str, image_name: str):
    """
    获取文档解析后的图片
    """
    doc = storage.get_document(document_id)
    if not doc:
        raise HTTPException(status_code=404, detail="文档不存在")

    # 构建图片路径
    # MinerU 输出目录结构: parsed_output/{文件名}/vlm/images/{image_name}
    # 需要从文件名中提取时间戳和文件名
    file_path = doc.get("filePath", "")
    file_name = Path(file_path).stem  # 获取不带扩展名的文件名

    # 尝试多个可能的路径
    possible_paths = [
        # 使用完整文件名
        os.path.join(settings.MINERU_OUTPUT_DIR, file_name, "vlm", "images", image_name),
        os.path.join(settings.MINERU_OUTPUT_DIR, file_name, "auto", "images", image_name),
        # 直接在输出目录下搜索
    ]

    image_path = None
    for path in possible_paths:
        if os.path.exists(path):
            image_path = path
            break

    # 如果没找到，尝试在整个输出目录中搜索
    if not image_path:
        for root, dirs, files in os.walk(settings.MINERU_OUTPUT_DIR):
            if image_name in files:
                image_path = os.path.join(root, image_name)
                break

    if not image_path or not os.path.exists(image_path):
        raise HTTPException(status_code=404, detail=f"图片不存在: {image_name}")

    # 根据文件扩展名确定媒体类型
    ext = Path(image_path).suffix.lower()
    media_type = "image/jpeg"
    if ext == ".png":
        media_type = "image/png"
    elif ext == ".gif":
        media_type = "image/gif"

    return FileResponse(
        image_path,
        media_type=media_type
    )


# ==================== RAG 分块和向量化相关接口 ====================

from app.services.chunker import chunker
from app.services.embedding import embedding_service
from app.services.vector_store import vector_store


@router.post("/{document_id}/chunk")
async def chunk_document(document_id: str):
    """
    对文档进行分块

    将 Markdown 文档按标题层级和内容智能分块
    """
    doc = storage.get_document(document_id)
    if not doc:
        raise HTTPException(status_code=404, detail="文档不存在")

    markdown_content = doc.get("markdownContent")
    if not markdown_content:
        raise HTTPException(status_code=400, detail="文档未解析，无法分块")

    try:
        # 执行分块
        chunks = chunker.chunk(markdown_content, document_id)

        # 转换为字典格式
        chunk_dicts = []
        for chunk in chunks:
            chunk_dicts.append({
                "id": chunk.id,
                "content": chunk.content,
                "title": chunk.title,
                "level": chunk.level,
                "chunk_index": chunk.chunk_index,
                "document_id": document_id
            })

        # 更新分块状态
        storage.update_chunked_status(document_id, True)

        return {
            "documentId": document_id,
            "chunkCount": len(chunk_dicts),
            "chunks": chunk_dicts
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"分块失败: {str(e)}")


@router.get("/{document_id}/chunks")
async def get_document_chunks(document_id: str):
    """
    获取文档的所有分块

    返回已存储在向量数据库中的文档块
    """
    try:
        # 确保向量数据库已连接
        if not vector_store.connected:
            vector_store.connect()

        chunks = vector_store.get_document_chunks(document_id)

        return {
            "documentId": document_id,
            "chunkCount": len(chunks),
            "chunks": chunks
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取分块失败: {str(e)}")


@router.post("/{document_id}/vectorize")
async def vectorize_document(document_id: str):
    """
    对文档进行分块并向量化存储（后台任务）

    流程：
    1. 对 Markdown 文档分块
    2. 使用 Ollama 生成向量
    3. 存储到 Milvus 向量数据库
    """
    doc = storage.get_document(document_id)
    if not doc:
        raise HTTPException(status_code=404, detail="文档不存在")

    markdown_content = doc.get("markdownContent")
    if not markdown_content:
        raise HTTPException(status_code=400, detail="文档未解析，无法分块")

    # 更新状态为处理中
    storage.update_vectorize_status(document_id, "processing")

    # 提交后台任务
    task_id = f"vectorize_{document_id}"

    async def vectorize_task():
        """向量化任务"""
        try:
            # 1. 分块
            chunks_data = chunker.chunk(markdown_content, document_id)

            if not chunks_data:
                storage.update_vectorize_status(document_id, "error")
                return

            # 2. 生成向量（同时返回成功的索引）
            texts = [chunk.content for chunk in chunks_data]
            successful_indices, embeddings = embedding_service.encode_with_indices(texts)

            # 检查是否有成功编码的向量
            if len(embeddings) == 0:
                storage.update_vectorize_status(document_id, "error")
                print("向量化任务失败: 没有成功编码任何文本")
                return

            # 只保留成功编码的分块
            successful_chunks = [chunks_data[i] for i in successful_indices]

            # 3. 存储到向量数据库
            if not vector_store.connected:
                vector_store.connect()

            # 创建集合（如果不存在）
            vector_store.create_collection(
                dimension=embedding_service.dimension,
                drop_existing=False
            )

            # 先删除该文档的旧块（避免残留）
            try:
                vector_store.delete_document(document_id)
                print(f"已删除文档 {document_id} 的旧向量数据")
            except Exception as e:
                print(f"删除旧块时出错（可能首次向量化）: {e}")

            # 准备数据（只包含成功编码的分块）
            chunk_dicts = [
                {
                    "id": chunk.id,
                    "document_id": document_id,
                    "chunk_index": idx,
                    "title": chunk.title,
                    "content": chunk.content,
                    "level": chunk.level
                }
                for idx, chunk in enumerate(successful_chunks)
            ]

            # 插入向量
            vector_store.insert_chunks(chunk_dicts, embeddings.tolist())

            # 更新状态为成功
            storage.update_vectorize_status(document_id, "success", len(chunk_dicts))

            # 4. 释放 GPU 显存
            embedding_service.unload_model()

        except Exception as e:
            storage.update_vectorize_status(document_id, "error")
            print(f"向量化任务失败: {e}")
            import traceback
            traceback.print_exc()
            # 即使失败也尝试释放GPU
            try:
                embedding_service.unload_model()
            except:
                pass

    # 提交到后台任务管理器
    from app.services.task_manager import task_manager
    await task_manager.submit_task(task_id, vectorize_task)

    return {
        "taskId": task_id,
        "message": "向量化任务已提交，正在后台处理"
    }


@router.get("/{document_id}/vectorize/status")
async def get_vectorize_status(document_id: str):
    """获取向量化任务状态"""
    doc = storage.get_document(document_id)
    if not doc:
        raise HTTPException(status_code=404, detail="文档不存在")

    return {
        "documentId": document_id,
        "status": doc.get("vectorizeStatus", "pending"),
        "chunked": doc.get("chunked", False),
        "chunkCount": doc.get("chunkCount")
    }


@router.post("/{document_id}/search")
async def search_chunks(
    document_id: str,
    query: str = Query(..., description="搜索查询文本"),
    top_k: int = Query(10, description="返回结果数量")
):
    """
    在文档中搜索相关内容

    使用向量相似度搜索文档块
    """
    try:
        # 测试 Ollama 连接
        if not embedding_service.test_connection():
            raise HTTPException(status_code=503, detail="Ollama 服务不可用")

        # 生成查询向量
        query_vector = embedding_service.encode_single(query)

        # 向量搜索
        if not vector_store.connected:
            vector_store.connect()

        results = vector_store.search(query_vector, top_k, document_id)

        return {
            "query": query,
            "documentId": document_id,
            "resultCount": len(results),
            "results": results
        }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"搜索失败: {str(e)}")


@router.post("/folders/{folder_id}/batch-vectorize")
async def batch_vectorize_folder(folder_id: str, mode: dict = None):
    """
    批量向量化知识库中的所有文档

    对指定知识库下的所有文档进行分块和向量化处理

    mode参数:
    - incremental: 增量处理，只处理未向量化的文档（默认）
    - full: 清空重建，删除所有现有结果后重新处理
    """
    try:
        # 解析模式
        if mode is None:
            mode = {}
        process_mode = mode.get("mode", "incremental")  # 默认增量模式

        # 获取知识库下的所有文档
        documents, total = storage.list_documents(folder=folder_id, skip=0, limit=1000)

        if total == 0:
            return {
                "folderId": folder_id,
                "totalCount": 0,
                "vectorizedCount": 0,
                "skippedCount": 0,
                "message": "知识库中没有文档"
            }

        # 统计
        vectorized_count = 0
        skipped_count = 0
        already_vectorized = 0

        # 提交批量向量化任务
        task_id = f"batch_vectorize_{folder_id}"

        async def batch_vectorize_task():
            """批量向量化任务"""
            nonlocal vectorized_count, skipped_count, already_vectorized

            # 如果是清空重建模式，先删除所有文档的向量数据
            if process_mode == "full":
                print(f"清空重建模式：开始删除知识库 {folder_id} 中所有文档的向量数据")
                for doc in documents:
                    doc_id = doc["id"]
                    try:
                        vector_store.delete_document(doc_id)
                        print(f"已删除文档 {doc_id} 的向量数据")
                        # 重置文档的向量化状态
                        storage.update_vectorize_status(doc_id, "pending", None)
                    except Exception as e:
                        print(f"删除文档 {doc_id} 的向量数据时出错: {e}")

                print(f"清空完成，开始重新处理所有文档")

            for doc in documents:
                doc_id = doc["id"]
                markdown_content = doc.get("markdownContent")

                # 检查是否已解析
                if not markdown_content:
                    skipped_count += 1
                    print(f"文档 {doc_id} 未解析，跳过")
                    continue

                # 增量模式：检查是否已向量化
                if process_mode == "incremental":
                    if doc.get("vectorizeStatus") == "success" and doc.get("chunked"):
                        already_vectorized += 1
                        print(f"文档 {doc_id} 已向量化，跳过")
                        continue

                try:
                    # 更新状态为处理中
                    storage.update_vectorize_status(doc_id, "processing")

                    # 1. 分块
                    chunks_data = chunker.chunk(markdown_content, doc_id)

                    if not chunks_data:
                        storage.update_vectorize_status(doc_id, "error")
                        skipped_count += 1
                        continue

                    # 2. 生成向量
                    texts = [chunk.content for chunk in chunks_data]
                    successful_indices, embeddings = embedding_service.encode_with_indices(texts)

                    if len(embeddings) == 0:
                        storage.update_vectorize_status(doc_id, "error")
                        skipped_count += 1
                        continue

                    # 只保留成功编码的分块
                    successful_chunks = [chunks_data[i] for i in successful_indices]

                    # 3. 存储到向量数据库
                    if not vector_store.connected:
                        vector_store.connect()

                    # 创建集合（如果不存在）
                    vector_store.create_collection(
                        dimension=embedding_service.dimension,
                        drop_existing=False
                    )

                    # 先删除该文档的旧块（如果是full模式，前面已经删除过了，这里会失败但不影响）
                    try:
                        vector_store.delete_document(doc_id)
                    except Exception as e:
                        print(f"删除文档 {doc_id} 的旧块时出错: {e}")

                    # 准备数据
                    chunk_dicts = [
                        {
                            "id": chunk.id,
                            "document_id": doc_id,
                            "chunk_index": idx,
                            "title": chunk.title,
                            "content": chunk.content,
                            "level": chunk.level
                        }
                        for idx, chunk in enumerate(successful_chunks)
                    ]

                    # 插入向量
                    vector_store.insert_chunks(chunk_dicts, embeddings.tolist())

                    # 更新状态为成功
                    storage.update_vectorize_status(doc_id, "success", len(chunk_dicts))
                    vectorized_count += 1

                    print(f"文档 {doc_id} 向量化完成，共 {len(chunk_dicts)} 个块")

                except Exception as e:
                    storage.update_vectorize_status(doc_id, "error")
                    skipped_count += 1
                    print(f"文档 {doc_id} 向量化失败: {e}")
                    import traceback
                    traceback.print_exc()

            # 释放 GPU 显存
            try:
                embedding_service.unload_model()
            except:
                pass

            print(f"批量向量化完成：向量化 {vectorized_count} 个，已存在 {already_vectorized} 个，跳过 {skipped_count} 个")

        # 提交到后台任务管理器
        from app.services.task_manager import task_manager
        await task_manager.submit_task(task_id, batch_vectorize_task)

        mode_text = "清空重建" if process_mode == "full" else "增量处理"
        return {
            "taskId": task_id,
            "folderId": folder_id,
            "totalCount": total,
            "alreadyVectorized": already_vectorized,
            "pendingVectorization": total - already_vectorized if process_mode == "incremental" else total,
            "message": f"{mode_text}任务已提交，共 {total} 个文档" + (f"，其中 {total - already_vectorized} 个需要处理" if process_mode == "incremental" else "")
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"批量向量化失败: {str(e)}")
