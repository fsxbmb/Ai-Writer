"""
应用配置
"""
from pydantic_settings import BaseSettings
from typing import List
import json


class Settings(BaseSettings):
    """应用配置类"""

    # 应用信息
    APP_NAME: str = "AI Writer Backend"
    APP_VERSION: str = "0.0.1"
    DEBUG: bool = True

    # 服务器配置
    HOST: str = "0.0.0.0"
    PORT: int = 8000

    # CORS 配置
    CORS_ORIGINS: List[str] = ["http://localhost:5173", "http://127.0.0.1:5173"]

    # 文件存储配置
    UPLOAD_DIR: str = "./uploads"
    PARSE_OUTPUT_DIR: str = "./parsed_data"
    MAX_UPLOAD_SIZE: int = 104857600  # 100MB

    # MinerU 配置
    MINERU_BACKEND: str = "pipeline"  # 使用 pipeline 进行快速轻量级解析
    MINERU_OUTPUT_DIR: str = "./parsed_output"
    MINERU_LANG: str = "ch"

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"

    @property
    def CORS_ORIGINS_list(self) -> List[str]:
        """解析 CORS_ORIGINS"""
        if isinstance(self.CORS_ORIGINS, str):
            try:
                return json.loads(self.CORS_ORIGINS)
            except json.JSONDecodeError:
                return [origin.strip() for origin in self.CORS_ORIGINS.split(",")]
        return self.CORS_ORIGINS


settings = Settings()
