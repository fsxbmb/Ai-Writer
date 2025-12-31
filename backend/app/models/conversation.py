"""
对话数据模型（使用 JSON 文件存储）
"""
import json
import os
from datetime import datetime
from typing import List, Optional, Dict
import uuid


class ConversationStorage:
    """对话存储类（基于 JSON 文件）"""

    def __init__(self, storage_dir: str = "./data"):
        self.storage_dir = storage_dir
        self.conversations_file = os.path.join(storage_dir, "conversations.json")
        self._ensure_storage_dir()

    def _ensure_storage_dir(self):
        """确保存储目录存在"""
        os.makedirs(self.storage_dir, exist_ok=True)
        if not os.path.exists(self.conversations_file):
            with open(self.conversations_file, "w", encoding="utf-8") as f:
                json.dump([], f, ensure_ascii=False, indent=2)

    def _load_conversations(self) -> List[Dict]:
        """加载对话数据"""
        with open(self.conversations_file, "r", encoding="utf-8") as f:
            return json.load(f)

    def _save_conversations(self, conversations: List[Dict]):
        """保存对话数据"""
        with open(self.conversations_file, "w", encoding="utf-8") as f:
            json.dump(conversations, f, ensure_ascii=False, indent=2)

    def create_conversation(
        self,
        title: str,
        folder_id: str,
        first_message: Dict
    ) -> Dict:
        """创建对话"""
        conversations = self._load_conversations()

        conversation = {
            "id": str(uuid.uuid4()),
            "title": title,
            "folderId": folder_id,
            "createdAt": datetime.now().isoformat(),
            "updatedAt": datetime.now().isoformat(),
            "messages": [first_message]
        }

        conversations.insert(0, conversation)  # 新对话放在最前面
        self._save_conversations(conversations)
        return conversation

    def get_conversation(self, conversation_id: str) -> Optional[Dict]:
        """获取单个对话"""
        conversations = self._load_conversations()
        for conv in conversations:
            if conv["id"] == conversation_id:
                return conv
        return None

    def list_conversations(
        self,
        folder_id: Optional[str] = None,
        limit: int = 50
    ) -> List[Dict]:
        """列出对话"""
        conversations = self._load_conversations()

        # 筛选
        if folder_id:
            conversations = [c for c in conversations if c["folderId"] == folder_id]

        return conversations[:limit]

    def add_message(
        self,
        conversation_id: str,
        role: str,
        content: str,
        sources: List[Dict] = None
    ) -> Optional[Dict]:
        """添加消息到对话"""
        conversations = self._load_conversations()

        for i, conv in enumerate(conversations):
            if conv["id"] == conversation_id:
                message = {
                    "id": str(uuid.uuid4()),
                    "role": role,  # "user" or "assistant"
                    "content": content,
                    "sources": sources or [],
                    "timestamp": datetime.now().isoformat()
                }
                conv["messages"].append(message)
                conv["updatedAt"] = datetime.now().isoformat()

                # 更新标题（使用第一条用户消息的前30个字符）
                if len(conv["messages"]) == 1 and role == "user":
                    conv["title"] = content[:30] + ("..." if len(content) > 30 else "")

                conversations[i] = conv
                self._save_conversations(conversations)
                return conv

        return None

    def delete_conversation(self, conversation_id: str) -> bool:
        """删除对话"""
        conversations = self._load_conversations()

        for i, conv in enumerate(conversations):
            if conv["id"] == conversation_id:
                conversations.pop(i)
                self._save_conversations(conversations)
                return True

        return False


# 全局存储实例
conversation_storage = ConversationStorage()
