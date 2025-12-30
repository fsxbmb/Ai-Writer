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

    return DocumentResponse(**doc)


@router.delete("/{document_id}")
async def delete_document(document_id: str):
    """
    删除文档
    """
    success = storage.delete_document(document_id)
    if not success:
        raise HTTPException(status_code=404, detail="文档不存在")

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
