"""
文件夹相关 API 路由
"""
from fastapi import APIRouter, HTTPException
from typing import List

from app.schemas.document import FolderCreate, FolderResponse
from app.models.document import storage
import uuid
from datetime import datetime

router = APIRouter()


@router.get("", response_model=List[FolderResponse])
async def list_folders():
    """
    获取文件夹列表
    """
    # 排除根目录
    folders = [f for f in storage.folders if f["id"] != "root"]
    return folders


@router.post("", response_model=FolderResponse)
async def create_folder(data: FolderCreate):
    """
    创建文件夹
    """
    import json

    # 生成新 ID
    folder_id = str(uuid.uuid4())

    # 创建文件夹对象
    folder = {
        "id": folder_id,
        "name": data.name,
        "parentId": data.parentId,
        "createdAt": datetime.now().isoformat(),
    }

    # 保存到存储
    storage.folders.append(folder)

    # 保存到文件
    with open(storage.folders_file, "w", encoding="utf-8") as f:
        json.dump(storage.folders, f, ensure_ascii=False, indent=2)

    return FolderResponse(**folder)


@router.delete("/{folder_id}")
async def delete_folder(folder_id: str):
    """
    删除文件夹
    """
    import json

    # 检查是否有文档在该文件夹中
    documents, _ = storage.list_documents(folder=folder_id)
    if documents:
        raise HTTPException(
            status_code=400, detail="该文件夹中还有文档，无法删除"
        )

    # 删除文件夹
    storage.folders = [f for f in storage.folders if f["id"] != folder_id]

    # 保存到文件
    with open(storage.folders_file, "w", encoding="utf-8") as f:
        json.dump(storage.folders, f, ensure_ascii=False, indent=2)

    return {"message": "删除成功"}
