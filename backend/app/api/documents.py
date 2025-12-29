"""
文档相关 API 路由
"""
import os
import shutil
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


@router.post("/{document_id}/parse", response_model=ParseResponse)
async def parse_document(document_id: str):
    """
    解析文档（调用 MinerU）
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

    # 调用 MinerU 解析
    markdown_content, error_message, images = await mineru_service.parse_pdf(
        file_path, document_id
    )

    # 更新解析结果
    if error_message:
        storage.update_parse_status(
            document_id, ParseStatus.ERROR, error_message=error_message
        )
        raise HTTPException(status_code=500, detail=f"解析失败: {error_message}")

    storage.update_parse_status(
        document_id, ParseStatus.SUCCESS, markdown_content=markdown_content
    )

    return ParseResponse(
        documentId=document_id,
        markdownContent=markdown_content,
        images=images,
    )


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
    document_id: str, markdownContent: str
):
    """
    更新文档内容
    """
    doc = storage.update_document(
        document_id, DocumentUpdate(markdownContent=markdownContent)
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
    document_id: str, format: str = Query("markdown", description="下载格式：pdf, markdown")
):
    """
    下载文档
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
        # 下载原始 PDF 文件
        file_path = doc.get("filePath")
        if not file_path or not os.path.exists(file_path):
            raise HTTPException(status_code=404, detail="文件不存在")

        return FileResponse(
            file_path,
            media_type="application/pdf",
            filename=doc["fileName"],
        )

    else:
        raise HTTPException(status_code=400, detail="不支持的格式")
