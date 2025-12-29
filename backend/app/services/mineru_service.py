"""
MinerU 文档解析服务
"""
import os
import asyncio
from pathlib import Path
from typing import Optional, Tuple
import logging

# 导入 MinerU API
# 注意：需要将 MinerU 目录添加到 Python 路径
import sys
mineru_path = "/data/songbinbin/Proj/Proj_051/AI_Writer/MinerU"
if mineru_path not in sys.path:
    sys.path.insert(0, mineru_path)

try:
    from mineru_api_simple import MinerUParser
except ImportError:
    # 如果导入失败，使用模拟版本
    MinerUParser = None
    logging.warning("MinerU 未安装，使用模拟解析器")

from app.core.config import settings

logger = logging.getLogger(__name__)


class MinerUService:
    """MinerU 解析服务"""

    def __init__(self):
        self.parser = None
        self.output_dir = settings.MINERU_OUTPUT_DIR
        self._init_parser()

    def _init_parser(self):
        """初始化解析器"""
        if MinerUParser is None:
            logger.warning("MinerU 未安装，使用模拟模式")
            return

        try:
            # 确保输出目录存在
            os.makedirs(self.output_dir, exist_ok=True)

            # 创建 MinerU 解析器
            self.parser = MinerUParser(
                backend=settings.MINERU_BACKEND,
                output_dir=self.output_dir,
                lang=settings.MINERU_LANG,
                formula_enable=True,
                table_enable=True,
            )
            logger.info(f"MinerU 解析器初始化成功，backend: {settings.MINERU_BACKEND}")
        except Exception as e:
            logger.error(f"MinerU 解析器初始化失败: {e}")
            self.parser = None

    async def parse_pdf(
        self, pdf_path: str, document_id: str
    ) -> Tuple[Optional[str], Optional[str], Optional[list]]:
        """
        解析 PDF 文件

        Args:
            pdf_path: PDF 文件路径
            document_id: 文档 ID

        Returns:
            (markdown_content, error_message, image_list)
        """
        if self.parser is None:
            # 模拟解析
            return await self._mock_parse(pdf_path, document_id)

        try:
            logger.info(f"开始解析 PDF: {pdf_path}")

            # 同步调用 MinerU（在异步上下文中使用 run_in_executor）
            loop = asyncio.get_event_loop()
            output_path = await loop.run_in_executor(
                None, self.parser.parse, pdf_path
            )

            # 读取解析结果
            markdown_content, images = await self._read_parse_result(
                output_path, pdf_path
            )

            logger.info(f"PDF 解析完成: {pdf_path}")
            return markdown_content, None, images

        except Exception as e:
            logger.error(f"PDF 解析失败: {e}")
            return None, str(e), []

    async def _read_parse_result(
        self, output_path: str, original_pdf_path: str
    ) -> Tuple[str, list]:
        """读取解析结果"""
        output_dir = Path(output_path)

        # 查找 Markdown 文件
        md_files = list(output_dir.rglob("*.md"))

        if not md_files:
            # 如果没有找到，返回默认内容
            return f"# {Path(original_pdf_path).stem}\n\n解析完成，但未找到 Markdown 文件。", []

        md_file = md_files[0]

        # 读取 Markdown 内容
        with open(md_file, "r", encoding="utf-8") as f:
            markdown_content = f.read()

        # 查找图片
        images_dir = md_file.parent / "images"
        images = []
        if images_dir.exists():
            for img_file in images_dir.iterdir():
                if img_file.is_file() and img_file.suffix.lower() in [
                    ".png",
                    ".jpg",
                    ".jpeg",
                    ".gif",
                ]:
                    images.append(str(img_file))

        return markdown_content, images

    async def _mock_parse(
        self, pdf_path: str, document_id: str
    ) -> Tuple[str, None, list]:
        """模拟解析（当 MinerU 不可用时）"""
        import time

        # 模拟解析延迟
        await asyncio.sleep(2)

        file_name = Path(pdf_path).stem

        # 生成模拟 Markdown 内容
        markdown_content = f"""# {file_name}

这是文档 **{file_name}** 的解析结果。

> 注意：由于 MinerU 未正确安装，这是模拟解析结果。

## 第一章

这是第一章的内容...

## 第二章

这是第二章的内容...

- 列表项 1
- 列表项 2
- 列表项 3

## 表格示例

| 列 1 | 列 2 | 列 3 |
|------|------|------|
| 数据 1 | 数据 2 | 数据 3 |
| 数据 4 | 数据 5 | 数据 6 |

---

*解析时间：{time.strftime("%Y-%m-%d %H:%M:%S")}*
"""

        return markdown_content, None, []


# 全局服务实例
mineru_service = MinerUService()
