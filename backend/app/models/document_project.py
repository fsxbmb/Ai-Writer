"""
文档项目数据模型（使用 JSON 文件存储）
"""
import json
import os
from datetime import datetime
from typing import List, Optional, Dict
import uuid


class DocumentProjectStorage:
    """文档项目存储类（基于 JSON 文件）"""

    def __init__(self, storage_dir: str = "./data"):
        self.storage_dir = storage_dir
        self.projects_file = os.path.join(storage_dir, "document_projects.json")
        self._ensure_storage_dir()

    def _ensure_storage_dir(self):
        """确保存储目录存在"""
        os.makedirs(self.storage_dir, exist_ok=True)
        if not os.path.exists(self.projects_file):
            with open(self.projects_file, "w", encoding="utf-8") as f:
                json.dump([], f, ensure_ascii=False, indent=2)

    def _load_projects(self) -> List[Dict]:
        """加载项目数据"""
        with open(self.projects_file, "r", encoding="utf-8") as f:
            return json.load(f)

    def _save_projects(self, projects: List[Dict]):
        """保存项目数据"""
        with open(self.projects_file, "w", encoding="utf-8") as f:
            json.dump(projects, f, ensure_ascii=False, indent=2)

    def create_project(
        self,
        title: str,
        folder_ids: List[str],
        outline: Optional[List[Dict]] = None,
        content: Optional[List[Dict]] = None,
    ) -> Dict:
        """创建项目"""
        projects = self._load_projects()

        # 初始化 sections
        sections = {}

        # 如果传入了 content，填充到 sections
        if content:
            for section_data in content:
                section_id = section_data.get("sectionId")
                if section_id:
                    sections[section_id] = section_data

        project = {
            "id": str(uuid.uuid4()),
            "title": title,
            "folderIds": folder_ids,
            "outline": outline,  # 大纲（树形结构）
            "outlineLocked": False,  # 大纲是否已锁定
            "sections": sections,  # 章节 ID -> 章节内容（包含段落和版本）
            "createdAt": datetime.now().isoformat(),
            "updatedAt": datetime.now().isoformat(),
        }

        projects.append(project)
        self._save_projects(projects)
        return project

    def get_project(self, project_id: str) -> Optional[Dict]:
        """获取单个项目"""
        projects = self._load_projects()
        for project in projects:
            if project["id"] == project_id:
                return project
        return None

    def list_projects(
        self,
        skip: int = 0,
        limit: int = 100,
    ) -> tuple[List[Dict], int]:
        """列出项目"""
        projects = self._load_projects()

        # 按更新时间倒序排序
        projects.sort(key=lambda x: x.get("updatedAt", ""), reverse=True)

        total = len(projects)

        # 分页
        projects = projects[skip : skip + limit]

        return projects, total

    def update_project(
        self,
        project_id: str,
        **update_data
    ) -> Optional[Dict]:
        """更新项目"""
        projects = self._load_projects()

        for i, project in enumerate(projects):
            if project["id"] == project_id:
                # 更新字段
                for key, value in update_data.items():
                    if key == "sections":
                        # 合并 sections
                        project["sections"].update(value)
                    else:
                        project[key] = value

                project["updatedAt"] = datetime.now().isoformat()
                projects[i] = project
                self._save_projects(projects)
                return project

        return None

    def update_outline(
        self,
        project_id: str,
        outline: List[Dict],
        locked: bool = False,
    ) -> Optional[Dict]:
        """更新大纲"""
        return self.update_project(project_id, outline=outline, outlineLocked=locked)

    def add_section_content(
        self,
        project_id: str,
        section_id: str,
        content: Dict,
    ) -> Optional[Dict]:
        """添加章节内容"""
        project = self.get_project(project_id)
        if not project:
            return None

        sections = project.get("sections", {})
        sections[section_id] = content
        return self.update_project(project_id, sections=sections)

    def update_paragraph(
        self,
        project_id: str,
        section_id: str,
        paragraph_id: str,
        content: str,
        save_version: bool = True,
    ) -> Optional[Dict]:
        """更新段落内容（支持版本管理）"""
        project = self.get_project(project_id)
        if not project:
            return None

        sections = project.get("sections", {})
        section = sections.get(section_id, {})
        paragraphs = section.get("paragraphs", [])

        # 找到段落（使用 paragraph_id 字段）
        for para in paragraphs:
            if para.get("paragraph_id") == paragraph_id:
                # 保存旧版本
                if save_version:
                    versions = para.get("versions", [])
                    versions.append({
                        "content": para.get("content", ""),
                        "timestamp": para.get("timestamp", datetime.now().isoformat()),
                    })
                    para["versions"] = versions

                # 更新内容
                para["content"] = content
                para["timestamp"] = datetime.now().isoformat()

                section["paragraphs"] = paragraphs
                sections[section_id] = section
                return self.update_project(project_id, sections=sections)

        return None

    def restore_paragraph_version(
        self,
        project_id: str,
        section_id: str,
        paragraph_id: str,
        version_index: int,
    ) -> Optional[Dict]:
        """恢复段落到指定版本"""
        project = self.get_project(project_id)
        if not project:
            return None

        sections = project.get("sections", {})
        section = sections.get(section_id, {})
        paragraphs = section.get("paragraphs", [])

        # 找到段落（使用 paragraph_id 字段）
        for para in paragraphs:
            if para.get("paragraph_id") == paragraph_id:
                versions = para.get("versions", [])
                if 0 <= version_index < len(versions):
                    # 保存当前版本
                    current_version = {
                        "content": para.get("content", ""),
                        "timestamp": para.get("timestamp", datetime.now().isoformat()),
                        "sources": para.get("sources", [])
                    }
                    versions.append(current_version)

                    # 恢复到指定版本
                    target_version = versions[version_index]
                    para["content"] = target_version.get("content", "")
                    para["timestamp"] = datetime.now().isoformat()

                    # 更新版本列表（移除被恢复的版本，因为它已成为当前版本）
                    para["versions"] = versions[:version_index] + versions[version_index + 1:]

                    section["paragraphs"] = paragraphs
                    sections[section_id] = section
                    return self.update_project(project_id, sections=sections)

        return None

    def delete_project(self, project_id: str) -> bool:
        """删除项目"""
        projects = self._load_projects()

        for i, project in enumerate(projects):
            if project["id"] == project_id:
                projects.pop(i)
                self._save_projects(projects)
                return True

        return False


# 全局存储实例
document_project_storage = DocumentProjectStorage()
