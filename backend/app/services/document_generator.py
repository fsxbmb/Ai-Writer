"""
文档生成服务
处理大纲生成、内容生成和Word导出
"""
import logging
import httpx
from typing import List, Dict, Optional
import json
import re
import uuid
from datetime import datetime

from app.services.rag import rag_service
from app.models.document import storage

logger = logging.getLogger(__name__)


class DocumentGeneratorService:
    """文档生成服务"""

    def __init__(
        self,
        ollama_base_url: str = "http://localhost:11434",
        llm_model: str = "qwen3:8b",
    ):
        self.ollama_base_url = ollama_base_url
        self.llm_model = llm_model
        self.client = httpx.Client(timeout=120.0)

    def generate_outline(
        self,
        topic: str,
        folder_ids: List[str],
    ) -> List[Dict]:
        """
        生成文档大纲

        Args:
            topic: 研究主题
            folder_ids: 知识库ID列表

        Returns:
            树形大纲结构
        """
        try:
            # 1. 获取所有文档ID
            all_document_ids = []
            for folder_id in folder_ids:
                documents, _ = storage.list_documents(folder=folder_id)
                all_document_ids.extend([doc["id"] for doc in documents])

            # 2. RAG检索相关内容
            context = ""
            if all_document_ids:
                logger.info(f"从 {len(all_document_ids)} 个文档中检索相关内容")
                chunks = rag_service.search_relevant_chunks(
                    query=topic,
                    document_ids=all_document_ids,
                    top_k=5
                )

                if chunks:
                    context_parts = []
                    for i, chunk in enumerate(chunks[:3], 1):
                        title = chunk.get("title", "无标题")
                        content = chunk.get("content", "")
                        context_parts.append(f"[参考{i}] {title}\n{content[:500]}...")

                    context = "\n\n".join(context_parts)

            # 3. 构建提示词 - 使用 Markdown 格式而不是 JSON
            if context:
                prompt = f"""请根据以下参考资料，为主题"{topic}"生成一个详细的文档大纲。

参考资料：
{context}

要求：
1. 大纲要层次分明，使用多级标题
2. 使用 Markdown 格式，# 号表示标题层级
3. 第一层用 ## 表示章节，第二层用 ### 表示小节，第三层用 - 表示要点
4. 请确保大纲全面且逻辑清晰

返回格式示例：
## 第一章 绪论
### 1.1 研究背景
- 背景要点1
- 背景要点2
### 1.2 研究意义
- 理论意义
- 实践意义

## 第二章 核心概念
### 2.1 基本概念
- 概念1
- 概念2

请只返回大纲内容，不要包含其他解释文字。"""
            else:
                prompt = f"""请为主题"{topic}"生成一个详细的文档大纲。

要求：
1. 大纲要层次分明，使用多级标题
2. 使用 Markdown 格式，# 号表示标题层级
3. 第一层用 ## 表示章节，第二层用 ### 表示小节，第三层用 - 表示要点

返回格式示例：
## 第一章 绪论
### 1.1 研究背景
- 背景要点1
- 背景要点2
### 1.2 研究意义
- 理论意义
- 实践意义

## 第二章 核心概念
### 2.1 基本概念
- 概念1
- 概念2

请只返回大纲内容，不要包含其他解释文字。"""

            # 4. 调用LLM生成大纲
            response = self.client.post(
                f"{self.ollama_base_url}/api/chat",
                json={
                    "model": self.llm_model,
                    "messages": [
                        {
                            "role": "system",
                            "content": "你是一个专业的文档大纲生成助手，擅长创建结构清晰、逻辑严密的文档大纲。"
                        },
                        {
                            "role": "user",
                            "content": prompt
                        }
                    ],
                    "stream": False,
                    "options": {
                        "temperature": 0.7,
                        "top_p": 0.9,
                        "num_predict": 2000
                    }
                },
                timeout=120.0
            )

            response.raise_for_status()
            result = response.json()
            content = result.get("message", {}).get("content", "")

            # 5. 解析 Markdown 格式的大纲
            outline = self._parse_outline_markdown(content)

            # 6. 为每个节点生成唯一ID
            outline = self._ensure_outline_ids(outline)

            logger.info(f"大纲生成成功，包含 {self._count_outline_nodes(outline)} 个节点")
            return outline

        except Exception as e:
            logger.error(f"大纲生成失败: {e}")
            raise

    def _parse_outline_markdown(self, content: str) -> List[Dict]:
        """解析 Markdown 格式的大纲"""
        logger.info(f"Markdown 内容:\n{content[:2000]}...")

        # 移除可能的 markdown 代码块标记
        if "```markdown" in content:
            content = content.split("```markdown")[1].split("```")[0].strip()
        elif "```" in content:
            content = content.split("```")[1].split("```")[0].strip()

        lines = content.strip().split('\n')
        outline = []
        stack = []  # (node_dict, level)
        node_counter = [0]  # 使用列表作为可变计数器，方便在嵌套函数中更新

        for line in lines:
            line = line.rstrip()
            if not line:
                continue

            # 跳过单独的 ---
            if line.strip() == '---':
                continue

            # 检测标题级别
            level = 0
            label = None

            if line.startswith('## '):
                level = 1  # 章节
                label = line[3:].strip()
            elif line.startswith('### '):
                level = 2  # 小节
                label = line[4:].strip()
            elif line.startswith('#### '):
                level = 3  # 要点
                label = line[5:].strip()
            elif line.startswith('- ') or line.startswith('* '):
                level = 3  # 要点（列表项）
                label = line[2:].strip()
            elif re.match(r'^\d+\.', line):
                # 数字开头的行，可能是章节
                level = 1
                label = line.strip()
            elif re.match(r'^\d+\.\d+\.', line):
                # 数字.数字 开头的行，可能是小节
                level = 2
                label = line.strip()
            else:
                # 其他行，如果是缩进的，可能是要点
                if line.startswith('    '):
                    level = 3
                    label = line.strip()
                else:
                    # 尝试作为章节处理
                    level = 1
                    label = line.strip()

            if not label:
                continue

            # 创建节点 - 使用全局计数器确保唯一性
            node_counter[0] += 1
            node = {
                "id": f"node-{node_counter[0]}",
                "label": label,
                "children": []
            }

            # 根据层级找到父节点
            while stack and stack[-1][1] >= level:
                stack.pop()

            if stack:
                stack[-1][0]["children"].append(node)
            else:
                outline.append(node)

            stack.append((node, level))

        logger.info(f"解析后的大纲节点数: {len(outline)}")
        return outline

    def _parse_outline_json(self, content: str) -> List[Dict]:
        """解析大纲JSON"""
        # 尝试提取JSON
        content = content.strip()

        logger.info(f"原始内容 (前2000字符):\n{content[:2000]}...")

        # 移除可能的markdown代码块标记
        if "```json" in content:
            content = content.split("```json")[1].split("```")[0].strip()
        elif "```" in content:
            content = content.split("```")[1].split("```")[0].strip()

        # 尝试找到JSON对象/数组的开始和结束
        json_start = -1
        json_end = -1

        # 找到第一个 { 或 [
        for i, char in enumerate(content):
            if char in ['{', '[']:
                json_start = i
                break

        if json_start >= 0:
            # 从这里开始，找到匹配的结束符
            stack = []
            start_char = content[json_start]
            end_char = '}' if start_char == '{' else ']'
            matching = {'{': '}', '[': ']', '}': '{', ']': '['}

            for i in range(json_start, len(content)):
                char = content[i]
                if char in ['{', '[']:
                    stack.append(char)
                elif char in ['}', ']']:
                    if stack and matching.get(stack[-1]) == char:
                        stack.pop()
                        if not stack:
                            json_end = i + 1
                            break

            if json_end > json_start:
                content = content[json_start:json_end]

        logger.info(f"提取后的JSON (前2000字符):\n{content[:2000]}...")

        # 尝试修复常见的JSON问题
        content = self._fix_json(content)

        # 尝试解析JSON
        try:
            outline = json.loads(content)

            # 如果是对象（单个根节点），转换为数组
            if isinstance(outline, dict):
                # 如果根节点有children，直接使用children
                if "children" in outline:
                    return outline["children"]
                # 否则包装成数组
                return [outline]

            if isinstance(outline, list):
                return outline

        except json.JSONDecodeError as e:
            logger.error(f"JSON解析失败: {e}")
            logger.error(f"错误位置附近的内容: {content[max(0, e.pos-200):e.pos+200]}")
            # 最后尝试使用文本解析
            logger.warning("尝试使用文本解析作为容错方案")
            return self._parse_outline_from_text(content)

    def _fix_json(self, json_str: str) -> str:
        """尝试修复常见的JSON格式问题"""
        # 移除控制字符（除了换行、制表符等）
        json_str = re.sub(r'[\x00-\x08\x0b-\x0c\x0e-\x1f\x7f-\x9f]', '', json_str)

        # 尝试修复未转义的换行符在字符串中
        # 这是一个常见问题，LLM经常在label中包含换行
        lines = json_str.split('\n')
        fixed_lines = []
        in_string = False
        escape_next = False

        for line in lines:
            fixed_line = []
            for char in line:
                if escape_next:
                    fixed_line.append(char)
                    escape_next = False
                    continue

                if char == '\\':
                    fixed_line.append(char)
                    escape_next = True
                elif char == '"' and not escape_next:
                    in_string = not in_string
                    fixed_line.append(char)
                elif char == '\n' and in_string:
                    # 在字符串中的换行，替换为 \\n
                    fixed_line.append('\\n')
                elif char == '\t' and in_string:
                    # 在字符串中的制表符，替换为 \\t
                    fixed_line.append('\\t')
                else:
                    fixed_line.append(char)

            fixed_lines.append(''.join(fixed_line))

        return '\n'.join(fixed_lines)

    def _parse_outline_from_text(self, text: str) -> List[Dict]:
        """从文本中解析大纲结构（容错方案）"""
        lines = text.strip().split("\n")
        outline = []
        stack = []  # (node, level)

        for line in lines:
            line = line.strip()
            if not line:
                continue

            # 检测标题级别
            level = 0
            if line.startswith("# "):
                level = 1
                label = line[2:].strip()
            elif line.startswith("## "):
                level = 2
                label = line[3:].strip()
            elif line.startswith("### "):
                level = 3
                label = line[4:].strip()
            elif line.startswith("#### "):
                level = 4
                label = line[5:].strip()
            elif re.match(r"^\d+\.", line):
                # 1. 章节标题
                level = 1
                label = line
            elif re.match(r"^\d+\.\d+\.", line):
                # 1.1 小节标题
                level = 2
                label = line
            elif re.match(r"^\d+\.\d+\.\d+\.", line):
                # 1.1.1 要点
                level = 3
                label = line
            elif line.startswith("- ") or line.startswith("• "):
                # 列表项
                level = 3
                label = line[2:].strip()
            else:
                # 默认级别
                level = 1
                label = line

            node = {
                "id": f"section-{len(outline)}-{level}",
                "label": label,
                "children": []
            }

            # 根据层级找到父节点
            while stack and stack[-1][1] >= level:
                stack.pop()

            if stack:
                stack[-1][0]["children"].append(node)
            else:
                outline.append(node)

            stack.append((node, level))

        return outline

    def _ensure_outline_ids(self, outline: List[Dict], parent_id: str = "") -> List[Dict]:
        """确保大纲节点有唯一ID"""
        for i, node in enumerate(outline):
            if not node.get("id"):
                node["id"] = f"{parent_id}section-{i}" if parent_id else f"section-{i}"

            if node.get("children"):
                node["children"] = self._ensure_outline_ids(
                    node["children"],
                    f"{node['id']}-"
                )

        return outline

    def _count_outline_nodes(self, outline: List[Dict]) -> int:
        """统计大纲节点数量"""
        count = 0
        for node in outline:
            count += 1
            if node.get("children"):
                count += self._count_outline_nodes(node["children"])
        return count

    def generate_section_content(
        self,
        section_title: str,
        section_id: str,
        document_ids: List[str],
        context_sections: List[str] = None
    ) -> Dict:
        """
        生成章节内容

        Args:
            section_title: 章节标题
            section_id: 章节ID
            document_ids: 知识库文档ID列表
            context_sections: 上下文章节（父级章节标题列表）

        Returns:
            生成的内容和引用
        """
        try:
            # 1. 构建查询（包含上下文）
            query = section_title
            if context_sections:
                query = " > ".join(context_sections + [section_title])

            # 2. RAG 检索相关内容
            sources = []
            if document_ids:
                logger.info(f"为章节 '{section_title}' 检索相关内容")
                chunks = rag_service.search_relevant_chunks(
                    query=query,
                    document_ids=document_ids,
                    top_k=3  # 取最相关的3个片段
                )

                # 只保留最高相似度的1个片段作为引用
                if chunks:
                    top_chunk = chunks[0]
                    doc_names = rag_service._get_document_names([top_chunk])

                    sources = [{
                        "id": top_chunk.get("id"),
                        "document_id": top_chunk.get("document_id"),
                        "document_name": doc_names.get(top_chunk.get("document_id"), "未知文档"),
                        "title": top_chunk.get("title"),
                        "content": top_chunk.get("content"),
                        "score": top_chunk.get("score", 0)
                    }]
                    logger.info(f"找到 {len(chunks)} 个相关片段，使用最相关的1个")

            # 3. 构建提示词
            prompt = self._build_content_prompt(section_title, sources, context_sections)

            # 4. 调用 LLM 生成内容
            response = self.client.post(
                f"{self.ollama_base_url}/api/chat",
                json={
                    "model": self.llm_model,
                    "messages": [
                        {
                            "role": "system",
                            "content": "你是一个专业的文档写作助手，擅长撰写结构清晰、内容丰富的文档章节。"
                        },
                        {
                            "role": "user",
                            "content": prompt
                        }
                    ],
                    "stream": False,
                    "options": {
                        "temperature": 0.7,
                        "top_p": 0.9,
                        "num_predict": 1500
                    }
                },
                timeout=120.0
            )

            response.raise_for_status()
            result = response.json()
            content = result.get("message", {}).get("content", "")

            logger.info(f"章节 '{section_title}' 内容生成完成，字数: {len(content)}")

            return {
                "paragraph_id": str(uuid.uuid4()),
                "section_id": section_id,
                "content": content,
                "sources": sources,
                "timestamp": datetime.now().isoformat()
            }

        except Exception as e:
            logger.error(f"生成章节内容失败: {e}")
            raise

    def regenerate_paragraph(
        self,
        section_title: str,
        section_id: str,
        document_ids: List[str],
        context_sections: List[str] = None
    ) -> Dict:
        """
        重新生成段落（用于段落重新生成功能）

        与 generate_section_content 相同，但明确为重新生成场景
        """
        return self.generate_section_content(
            section_title=section_title,
            section_id=section_id,
            document_ids=document_ids,
            context_sections=context_sections
        )

    def _build_content_prompt(
        self,
        section_title: str,
        sources: List[Dict],
        context_sections: List[str] = None
    ) -> str:
        """构建内容生成提示词"""
        # 构建上下文路径
        context_path = ""
        if context_sections:
            context_path = " > ".join(context_sections + [section_title])
        else:
            context_path = section_title

        # 构建参考资料部分
        reference = ""
        if sources:
            source = sources[0]
            reference = f"""
参考资料：
文档：{source['document_name']}
章节：{source['title']}
内容：{source['content'][:500]}...
"""
        else:
            reference = "参考资料：无（请基于通用知识撰写）"

        prompt = f"""请为文档的以下章节撰写内容：

章节路径：{context_path}

{reference}

要求：
1. 内容要详实、准确、有条理
2. 如果有参考资料，请充分参考资料内容
3. 使用清晰的段落结构
4. 字数控制在 500-1000 字
5. 不要包含章节标题本身

请撰写内容："""

        return prompt


# 全局服务实例
document_generator_service = DocumentGeneratorService()
