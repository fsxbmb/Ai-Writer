"""
Ollama服务管理 API
"""
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from app.services.ollama_controller import ollama_controller

router = APIRouter()


class StartOllamaRequest(BaseModel):
    """启动Ollama请求"""
    ollamaPath: str = Field(default="ollama", description="Ollama可执行文件路径")


@router.post("/start")
async def start_ollama(request: StartOllamaRequest = None):
    """
    启动Ollama服务

    启动Ollama服务，如果已经运行则返回成功
    """
    try:
        if request:
            ollama_controller.ollama_path = request.ollamaPath

        success = ollama_controller.start()
        if success:
            return {
                "message": "Ollama服务启动成功",
                "host": ollama_controller.host
            }
        else:
            raise HTTPException(status_code=500, detail="Ollama服务启动失败")

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"启动失败: {str(e)}")


@router.post("/stop")
async def stop_ollama():
    """
    停止Ollama服务

    停止Ollama服务并释放所有显存
    """
    try:
        success = ollama_controller.stop()
        if success:
            return {"message": "Ollama服务已停止"}
        else:
            raise HTTPException(status_code=500, detail="Ollama服务停止失败")

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"停止失败: {str(e)}")


@router.post("/restart")
async def restart_ollama():
    """
    重启Ollama服务

    重启Ollama服务，会释放所有显存后重新启动
    """
    try:
        success = ollama_controller.restart()
        if success:
            return {
                "message": "Ollama服务重启成功",
                "host": ollama_controller.host
            }
        else:
            raise HTTPException(status_code=500, detail="Ollama服务重启失败")

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"重启失败: {str(e)}")


@router.get("/status")
async def get_ollama_status():
    """
    获取Ollama服务状态

    返回Ollama服务是否运行以及已加载的模型信息
    """
    try:
        is_running = ollama_controller.is_running()
        models = ollama_controller.get_loaded_models() if is_running else []

        return {
            "running": is_running,
            "host": ollama_controller.host,
            "loaded_models": models,
            "model_count": len(models)
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取状态失败: {str(e)}")


@router.post("/unload")
async def unload_models():
    """
    卸载所有模型

    卸载Ollama中的所有模型，释放显存，但保持服务运行
    """
    try:
        success = ollama_controller.unload_all_models()
        if success:
            return {"message": "已卸载所有模型，显存已释放"}
        else:
            raise HTTPException(status_code=500, detail="卸载模型失败")

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"卸载失败: {str(e)}")
