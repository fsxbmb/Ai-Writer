"""
MinerU 文档解析服务
"""
import os
import sys
import asyncio
import subprocess
import json
from pathlib import Path
from typing import Optional, Tuple
import logging

logger = logging.getLogger(__name__)

from app.core.config import settings


class MinerUService:
    """MinerU 解析服务 - 使用子进程执行，确保资源释放"""

    def __init__(self):
        self.output_dir = settings.MINERU_OUTPUT_DIR
        self.parser_script = os.path.join(
            os.path.dirname(__file__),
            "mineru_parser.py"
        )

    async def parse_pdf(
        self, pdf_path: str, document_id: str
    ) -> Tuple[Optional[str], Optional[str], Optional[list]]:
        """
        解析 PDF 文件（在独立子进程中执行）

        流程：
        1. 在子进程中执行 MinerU 解析
        2. 子进程完成后自动退出，释放所有 GPU 资源
        3. 读取解析结果

        Args:
            pdf_path: PDF 文件路径
            document_id: 文档 ID

        Returns:
            (markdown_content, error_message, image_list)
        """
        # 确保输出目录存在
        os.makedirs(self.output_dir, exist_ok=True)

        logger.info(f"开始解析 PDF: {pdf_path}")
        logger.info(f"Backend: {settings.MINERU_BACKEND}")

        try:
            # 构建子进程命令
            cmd = [
                sys.executable,
                self.parser_script,
                "--pdf-path", pdf_path,
                "--output-dir", self.output_dir,
                "--backend", settings.MINERU_BACKEND,
                "--lang", settings.MINERU_LANG
            ]

            logger.info(f"执行命令: {' '.join(cmd)}")

            # 执行子进程（异步方式）
            process = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
                env=os.environ.copy()
            )

            # 等待进程完成
            stdout, stderr = await process.communicate()

            # 检查退出码
            if process.returncode != 0:
                error_msg = stderr.decode('utf-8') if stderr else "未知错误"
                logger.error(f"解析失败，退出码: {process.returncode}, 错误: {error_msg}")
                return None, error_msg, []

            # 解析输出结果
            try:
                result = json.loads(stdout.decode('utf-8'))

                if not result.get("success"):
                    error = result.get("error", "解析失败")
                    logger.error(f"解析失败: {error}")
                    return None, error, []

                markdown_content = result.get("markdown_content", "")
                images = result.get("images", [])

                logger.info(f"PDF 解析完成: {pdf_path}")
                logger.info(f"Markdown 长度: {len(markdown_content)}, 图片数: {len(images)}")

                return markdown_content, None, images

            except json.JSONDecodeError as e:
                logger.error(f"解析结果 JSON 格式错误: {e}")
                logger.error(f"原始输出: {stdout.decode('utf-8')[:500]}")
                return None, f"解析结果格式错误: {e}", []

        except Exception as e:
            logger.error(f"PDF 解析失败: {e}", exc_info=True)
            return None, str(e), []

# 全局服务实例
mineru_service = MinerUService()
