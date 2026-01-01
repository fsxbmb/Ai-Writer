"""
问答相关 API 路由
"""
from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel, Field
from typing import List, Optional
import uuid

from app.models.conversation import conversation_storage
from app.services.rag import rag_service, task_manager
from app.models.document import storage

router = APIRouter()


class QuestionRequest(BaseModel):
    """提问请求"""
    question: str = Field(..., description="问题内容")
    documentId: Optional[str] = Field(None, description="文档ID（已弃用，使用folderId）")
    folderId: Optional[str] = Field(None, description="知识库ID")
    conversationId: Optional[str] = Field(None, description="对话ID")
    taskId: Optional[str] = Field(None, description="任务ID，用于停止生成")


class AnswerResponse(BaseModel):
    """回答响应"""
    answer: str = Field(..., description="回答内容")
    sources: List[dict] = Field(default_factory=list, description="引用的文档块")


@router.post("/ask")
async def ask_question(request: QuestionRequest):
    """
    提问（RAG 问答）

    基于知识库内容回答问题，使用 RAG 技术检索相关资料并生成回答
    """
    # 创建任务
    task_id = request.taskId or str(uuid.uuid4())
    task_manager.create_task(task_id)

    try:
        # 获取对话历史
        conversation_history = None
        if request.conversationId:
            conversation = conversation_storage.get_conversation(request.conversationId)
            if conversation:
                conversation_history = conversation.get("messages", [])

        # 执行 RAG 问答
        result = rag_service.answer_question(
            query=request.question,
            document_id=request.documentId,
            document_ids=get_document_ids(request.folderId),
            conversation_id=request.conversationId,
            conversation_history=conversation_history,
            task_id=task_id
        )

        # 如果有对话ID，保存消息
        if request.conversationId:
            # 保存用户消息
            conversation_storage.add_message(
                request.conversationId,
                "user",
                request.question
            )

            # 保存助手消息
            conversation_storage.add_message(
                request.conversationId,
                "assistant",
                result["answer"],
                result["sources"]
            )

        return result

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"问答失败: {str(e)}")


def get_document_ids(folder_id: str) -> Optional[List[str]]:
    """获取知识库下的所有文档ID"""
    if not folder_id:
        return None

    documents, _ = storage.list_documents(folder=folder_id)
    if not documents:
        return None

    return [doc["id"] for doc in documents]


class CreateConversationRequest(BaseModel):
    """创建对话请求"""
    folderId: str = Field(..., description="知识库ID")
    firstQuestion: str = Field(..., description="第一个问题")
    taskId: Optional[str] = Field(None, description="任务ID，用于停止生成")


@router.post("/conversations")
async def create_conversation(request: CreateConversationRequest):
    """
    创建对话

    创建新的对话并自动回答第一个问题
    """
    # 创建任务
    task_id = request.taskId or str(uuid.uuid4())
    task_manager.create_task(task_id)

    try:
        # 创建对话（使用第一个问题作为标题）
        first_message = {
            "role": "user",
            "content": request.firstQuestion
        }

        conversation = conversation_storage.create_conversation(
            title=request.firstQuestion[:30],
            folder_id=request.folderId,
            first_message=first_message
        )

        # 回答问题
        result = rag_service.answer_question(
            query=request.firstQuestion,
            document_ids=get_document_ids(request.folderId),
            conversation_id=conversation["id"],
            conversation_history=None,
            task_id=task_id
        )

        # 保存助手回答
        conversation_storage.add_message(
            conversation["id"],
            "assistant",
            result["answer"],
            result["sources"]
        )

        return {
            "conversationId": conversation["id"],
            "answer": result["answer"],
            "sources": result["sources"]
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"创建对话失败: {str(e)}")


@router.get("/conversations")
async def list_conversations(
    folderId: str = Query(..., description="知识库ID"),
    limit: int = Query(20, description="返回数量")
):
    """
    获取对话列表

    获取指定知识库的所有对话
    """
    try:
        conversations = conversation_storage.list_conversations(
            folder_id=folderId,
            limit=limit
        )

        return {
            "conversations": conversations,
            "total": len(conversations)
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取对话列表失败: {str(e)}")


@router.get("/conversations/{conversation_id}")
async def get_conversation(conversation_id: str):
    """
    获取对话详情

    获取对话的所有消息历史
    """
    try:
        conversation = conversation_storage.get_conversation(conversation_id)
        if not conversation:
            raise HTTPException(status_code=404, detail="对话不存在")

        return conversation

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取对话失败: {str(e)}")


@router.delete("/conversations/{conversation_id}")
async def delete_conversation(conversation_id: str):
    """
    删除对话
    """
    try:
        success = conversation_storage.delete_conversation(conversation_id)
        if not success:
            raise HTTPException(status_code=404, detail="对话不存在")

        return {"message": "删除成功"}

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"删除对话失败: {str(e)}")


class StopGenerationRequest(BaseModel):
    """停止生成请求"""
    taskId: str = Field(..., description="任务ID")


@router.post("/stop")
async def stop_generation(request: StopGenerationRequest):
    """
    停止生成任务

    停止指定的问答生成任务并释放资源
    """
    try:
        success = task_manager.stop_task(request.taskId)
        if success:
            return {"message": "任务已停止", "taskId": request.taskId}
        else:
            # 任务不存在可能表示：1) 任务已完成 2) 任务还没开始 3) 任务ID错误
            # 无论是哪种情况，都返回成功，因为任务已经不在运行了
            return {"message": "任务已停止或已完成", "taskId": request.taskId}

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"停止任务失败: {str(e)}")

