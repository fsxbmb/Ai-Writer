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


def update_folder_timestamp(folder_id: str):
    """
    更新文件夹的时间戳

    当文件夹内的文档发生变化时（上传、删除、更新等），调用此函数更新 updatedAt
    """
    import json

    for i, folder in enumerate(storage.folders):
        if folder["id"] == folder_id:
            folder["updatedAt"] = datetime.now().isoformat()
            storage.folders[i] = folder

            # 保存到文件
            with open(storage.folders_file, "w", encoding="utf-8") as f:
                json.dump(storage.folders, f, ensure_ascii=False, indent=2)
            return


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
        "updatedAt": datetime.now().isoformat(),
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
    删除文件夹（级联删除所有文档）
    """
    import json

    # 获取文件夹中的所有文档
    documents, _ = storage.list_documents(folder=folder_id)

    # 级联删除所有文档
    for doc in documents:
        doc_id = doc["id"]
        # 删除文档文件
        storage.delete_document(doc_id)

    # 删除文件夹
    storage.folders = [f for f in storage.folders if f["id"] != folder_id]

    # 保存到文件
    with open(storage.folders_file, "w", encoding="utf-8") as f:
        json.dump(storage.folders, f, ensure_ascii=False, indent=2)

    return {"message": f"删除成功（已删除 {len(documents)} 个文档）"}
