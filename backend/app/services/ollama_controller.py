"""
Ollama服务控制器
用于启动、停止和管理Ollama服务
"""
import subprocess
import signal
import requests
import time
import logging
from typing import Optional

logger = logging.getLogger(__name__)


class OllamaController:
    """Ollama服务控制类"""

    def __init__(self, ollama_path: str = "ollama", host: str = "localhost:11434"):
        self.ollama_path = ollama_path
        self.host = host
        self.base_url = f"http://{host}"
        self.process: Optional[subprocess.Popen] = None

    def start(self) -> bool:
        """
        启动Ollama服务

        Returns:
            bool: 是否启动成功
        """
        if self.is_running():
            logger.info("Ollama服务已在运行")
            return True

        logger.info("启动Ollama服务...")
        try:
            self.process = subprocess.Popen(
                [self.ollama_path, "serve"],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                preexec_fn=lambda: signal.signal(signal.SIGINT, signal.SIG_IGN)
            )

            # 等待服务启动
            for i in range(30):
                try:
                    response = requests.get(f"{self.base_url}/api/tags", timeout=2)
                    if response.status_code == 200:
                        logger.info("Ollama服务启动成功")
                        return True
                except:
                    if i % 5 == 0:
                        logger.info(f"等待Ollama服务启动... ({i+1}/30)")
                    time.sleep(1)

            logger.error("Ollama服务启动超时")
            return False

        except Exception as e:
            logger.error(f"启动Ollama服务失败: {e}")
            return False

    def stop(self) -> bool:
        """
        停止Ollama服务，释放所有显存

        Returns:
            bool: 是否停止成功
        """
        if not self.process:
            logger.warning("Ollama服务未通过Python启动，无法停止")
            # 即使不是通过我们启动的，也可以尝试通过API停止
            return self.force_unload_all()

        logger.info("停止Ollama服务...")
        try:
            self.process.terminate()
            try:
                self.process.wait(timeout=10)
                logger.info("Ollama服务已正常停止")
            except subprocess.TimeoutExpired:
                logger.warning("Ollama服务未响应，强制终止")
                self.process.kill()
                self.process.wait()
                logger.info("Ollama服务已强制停止")

            self.process = None
            return True

        except Exception as e:
            logger.error(f"停止Ollama服务失败: {e}")
            return False

    def restart(self) -> bool:
        """
        重启Ollama服务

        Returns:
            bool: 是否重启成功
        """
        logger.info("重启Ollama服务...")
        self.stop()
        time.sleep(2)
        return self.start()

    def is_running(self) -> bool:
        """
        检查Ollama服务是否运行

        Returns:
            bool: 服务是否运行
        """
        try:
            response = requests.get(f"{self.base_url}/api/tags", timeout=2)
            return response.status_code == 200
        except:
            return False

    def get_loaded_models(self) -> list:
        """
        获取已加载的模型列表

        Returns:
            list: 模型列表
        """
        try:
            response = requests.get(f"{self.base_url}/api/tags", timeout=5)
            if response.status_code == 200:
                data = response.json()
                return data.get("models", [])
        except Exception as e:
            logger.error(f"获取模型列表失败: {e}")
        return []

    def unload_model(self, model_name: str) -> bool:
        """
        卸载指定模型，释放显存

        Args:
            model_name: 模型名称

        Returns:
            bool: 是否卸载成功
        """
        try:
            # 通过发送一个不保持活跃的请求来卸载模型
            response = requests.post(
                f"{self.base_url}/api/generate",
                json={
                    "model": model_name,
                    "prompt": "",
                    "stream": False,
                    "keep_alive": False  # 关键：不保持模型在内存中
                },
                timeout=10
            )
            logger.info(f"已卸载模型: {model_name}")
            return True
        except Exception as e:
            logger.error(f"卸载模型 {model_name} 失败: {e}")
            return False

    def unload_all_models(self) -> bool:
        """
        卸载所有模型，释放所有显存

        Returns:
            bool: 是否成功
        """
        models = self.get_loaded_models()
        logger.info(f"发现 {len(models)} 个已加载的模型")

        for model_info in models:
            model_name = model_info.get("name", "")
            if model_name:
                self.unload_model(model_name)

        return True

    def force_unload_all(self) -> bool:
        """
        强制释放所有显存（通过调用Ollama API）

        Returns:
            bool: 是否成功
        """
        try:
            # 获取所有运行中的进程
            response = requests.post(
                f"{self.base_url}/api/ps",
                json={},
                timeout=5
            )
            if response.status_code == 200:
                data = response.json()
                # 终止所有运行中的模型进程
                for process in data.get("models", []):
                    model_name = process.get("name", "")
                    logger.info(f"终止进程: {model_name}")

            # 卸载所有模型
            self.unload_all_models()
            return True

        except Exception as e:
            logger.error(f"强制卸载失败: {e}")
            return False


# 全局Ollama控制器实例
ollama_controller = OllamaController()
