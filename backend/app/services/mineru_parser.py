#!/usr/bin/env python3
"""
MinerU 解析执行脚本
在独立进程中执行，确保解析完成后释放所有 GPU 资源
"""
import sys
import os
import json
import argparse
from pathlib import Path

# 添加 MinerU 路径
mineru_path = "/data/songbinbin/Proj/Proj_051/AI_Writer/MinerU"
if mineru_path not in sys.path:
    sys.path.insert(0, mineru_path)

from mineru_api_simple import MinerUParser


def parse_pdf(pdf_path: str, output_dir: str, backend: str = "pipeline", lang: str = "ch"):
    """
    解析 PDF 文件

    Args:
        pdf_path: PDF 文件路径
        output_dir: 输出目录
        backend: MinerU 后端（pipeline, vlm-vllm 等）
        lang: 语言（ch, en 等）

    Returns:
        dict: 解析结果 {success: bool, markdown_content: str, images: list, error: str}
    """
    try:
        # 创建解析器
        parser = MinerUParser(
            backend=backend,
            output_dir=output_dir,
            lang=lang,
            formula_enable=True,
            table_enable=True,
        )

        # 执行解析（同步方式）
        output_path = parser.parse(pdf_path)

        # 读取解析结果
        output_dir_path = Path(output_path)
        md_files = list(output_dir_path.rglob("*.md"))

        if not md_files:
            return {
                "success": False,
                "error": f"未找到 Markdown 文件，输出目录: {output_path}",
                "markdown_content": "",
                "images": []
            }

        md_file = md_files[0]

        # 读取 Markdown 内容
        with open(md_file, "r", encoding="utf-8") as f:
            markdown_content = f.read()

        # 查找图片
        images_dir = md_file.parent / "images"
        images = []
        if images_dir.exists():
            for img_file in images_dir.iterdir():
                if img_file.is_file() and img_file.suffix.lower() in [".png", ".jpg", ".jpeg", ".gif"]:
                    images.append(img_file.name)

        return {
            "success": True,
            "markdown_content": markdown_content,
            "images": images,
            "error": None
        }

    except Exception as e:
        import traceback
        return {
            "success": False,
            "error": str(e),
            "traceback": traceback.format_exc(),
            "markdown_content": "",
            "images": []
        }


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="MinerU PDF 解析器")
    parser.add_argument("--pdf-path", required=True, help="PDF 文件路径")
    parser.add_argument("--output-dir", required=True, help="输出目录")
    parser.add_argument("--backend", default="pipeline", help="MinerU 后端")
    parser.add_argument("--lang", default="ch", help="语言")

    args = parser.parse_args()

    # 执行解析
    result = parse_pdf(
        pdf_path=args.pdf_path,
        output_dir=args.output_dir,
        backend=args.backend,
        lang=args.lang
    )

    # 输出结果（JSON 格式）
    print(json.dumps(result, ensure_ascii=False, indent=2))

    # 退出码
    sys.exit(0 if result["success"] else 1)
