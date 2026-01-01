"""
文档项目相关 API 路由
"""
from fastapi import APIRouter, HTTPException, Query
from fastapi.responses import StreamingResponse, HTMLResponse
from pydantic import BaseModel, Field
from typing import List, Optional
from docx import Document
from docx.shared import Pt, RGBColor, Inches
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.oxml.ns import qn  # 用于设置字体
import io
from urllib.parse import quote

from app.models.document_project import document_project_storage
from app.services.document_generator import document_generator_service

router = APIRouter()


class CreateProjectRequest(BaseModel):
    """创建项目请求"""
    title: str = Field(..., description="项目标题")
    folderIds: List[str] = Field(default=[], description="知识库ID列表")
    outline: Optional[List[dict]] = Field(None, description="大纲树形结构")
    content: Optional[List[dict]] = Field(None, description="章节内容")


class UpdateOutlineRequest(BaseModel):
    """更新大纲请求"""
    outline: List[dict] = Field(..., description="大纲树形结构")
    locked: bool = Field(False, description="是否锁定大纲")


class GenerateOutlineRequest(BaseModel):
    """生成大纲请求"""
    topic: str = Field(..., description="研究主题")


@router.post("")
async def create_project(request: CreateProjectRequest):
    """
    创建文档项目

    创建新的文档生成项目，可以选择多个知识库，也可以直接传入大纲和内容
    """
    try:
        project = document_project_storage.create_project(
            title=request.title,
            folder_ids=request.folderIds,
            outline=request.outline,
            content=request.content,
        )
        return project

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"创建项目失败: {str(e)}")


@router.get("")
async def list_projects(
    skip: int = Query(0, description="跳过数量"),
    limit: int = Query(20, description="返回数量")
):
    """
    获取项目列表

    获取所有文档项目
    """
    try:
        projects, total = document_project_storage.list_projects(
            skip=skip,
            limit=limit,
        )

        return {
            "projects": projects,
            "total": total
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取项目列表失败: {str(e)}")


@router.get("/{project_id}")
async def get_project(project_id: str):
    """
    获取项目详情

    获取项目的完整信息，包括大纲和内容
    """
    try:
        project = document_project_storage.get_project(project_id)
        if not project:
            raise HTTPException(status_code=404, detail="项目不存在")

        return project

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取项目失败: {str(e)}")


@router.put("/{project_id}/outline")
async def update_outline(project_id: str, request: UpdateOutlineRequest):
    """
    更新大纲

    更新项目的大纲并设置锁定状态
    """
    try:
        project = document_project_storage.get_project(project_id)
        if not project:
            raise HTTPException(status_code=404, detail="项目不存在")

        current_locked = project.get("outlineLocked", False)

        # 只有在当前已锁定且请求保持锁定状态时才拒绝修改
        # 允许解锁操作（locked=False）或首次锁定
        if current_locked and request.locked:
            raise HTTPException(status_code=400, detail="大纲已锁定，无法修改")

        updated_project = document_project_storage.update_outline(
            project_id=project_id,
            outline=request.outline,
            locked=request.locked,
        )

        return updated_project

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"更新大纲失败: {str(e)}")


@router.post("/{project_id}/generate-outline")
async def generate_outline(project_id: str, request: GenerateOutlineRequest):
    """
    生成大纲

    基于研究主题和知识库内容自动生成文档大纲
    """
    try:
        project = document_project_storage.get_project(project_id)
        if not project:
            raise HTTPException(status_code=404, detail="项目不存在")

        # 检查大纲是否已锁定
        if project.get("outlineLocked", False):
            raise HTTPException(status_code=400, detail="大纲已锁定，无法重新生成")

        # 生成大纲
        outline = document_generator_service.generate_outline(
            topic=request.topic,
            folder_ids=project.get("folderIds", []),
        )

        # 更新项目
        updated_project = document_project_storage.update_outline(
            project_id=project_id,
            outline=outline,
            locked=False,  # 生成后不锁定，需要用户确认
        )

        return updated_project

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"生成大纲失败: {str(e)}")


@router.delete("/{project_id}")
async def delete_project(project_id: str):
    """
    删除项目

    删除文档项目
    """
    try:
        success = document_project_storage.delete_project(project_id)
        if not success:
            raise HTTPException(status_code=404, detail="项目不存在")

        return {"message": "删除成功"}

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"删除项目失败: {str(e)}")


class GenerateContentRequest(BaseModel):
    """生成内容请求"""
    sectionId: str = Field(..., description="章节ID")
    sectionTitle: str = Field(..., description="章节标题")
    contextSections: List[str] = Field(default=[], description="上下文章节路径")
    customPrompt: str = Field(default="", description="自定义生成需求")


class RegenerateParagraphRequest(BaseModel):
    """重新生成段落请求"""
    sectionId: str = Field(..., description="章节ID")
    sectionTitle: str = Field(..., description="章节标题")
    contextSections: List[str] = Field(default=[], description="上下文章节路径")
    customPrompt: str = Field(default="", description="自定义生成需求")


class UpdateParagraphRequest(BaseModel):
    """更新段落请求"""
    sectionId: str = Field(..., description="章节ID")
    paragraphId: str = Field(..., description="段落ID")
    content: str = Field(..., description="段落内容")


@router.post("/{project_id}/generate-content")
async def generate_section_content(project_id: str, request: GenerateContentRequest):
    """
    生成章节内容

    为指定章节生成内容，基于RAG检索的相关内容
    """
    try:
        project = document_project_storage.get_project(project_id)
        if not project:
            raise HTTPException(status_code=404, detail="项目不存在")

        # 获取所有文档ID
        document_ids = []
        for folder_id in project.get("folderIds", []):
            from app.models.document import storage as doc_storage
            documents, _ = doc_storage.list_documents(folder=folder_id)
            document_ids.extend([doc["id"] for doc in documents])

        # 生成内容
        result = document_generator_service.generate_section_content(
            section_title=request.sectionTitle,
            section_id=request.sectionId,
            document_ids=document_ids,
            context_sections=request.contextSections if request.contextSections else None,
            custom_prompt=request.customPrompt if request.customPrompt else None
        )

        # 保存到项目
        document_project_storage.add_section_content(
            project_id=project_id,
            section_id=request.sectionId,
            content={
                "sectionId": request.sectionId,
                "paragraphs": [result],
                "sources": result.get("sources", [])
            }
        )

        return result

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"生成内容失败: {str(e)}")


@router.post("/{project_id}/regenerate-paragraph")
async def regenerate_paragraph(project_id: str, request: RegenerateParagraphRequest):
    """
    重新生成段落

    重新生成指定章节的段落内容，保存旧版本到versions中
    """
    try:
        project = document_project_storage.get_project(project_id)
        if not project:
            raise HTTPException(status_code=404, detail="项目不存在")

        # 获取所有文档ID
        document_ids = []
        for folder_id in project.get("folderIds", []):
            from app.models.document import storage as doc_storage
            documents, _ = doc_storage.list_documents(folder=folder_id)
            document_ids.extend([doc["id"] for doc in documents])

        # 获取当前段落（用于保存版本）
        sections = project.get("sections", {})
        section = sections.get(request.sectionId, {})
        paragraphs = section.get("paragraphs", [])

        # 准备当前段落信息和版本历史
        current_paragraph = None
        existing_versions = []

        if paragraphs:
            # 获取最新的段落
            current_paragraph = paragraphs[-1]
            # 获取已有的历史版本
            existing_versions = current_paragraph.get("versions", [])

        # 重新生成
        new_paragraph_data = document_generator_service.regenerate_paragraph(
            section_title=request.sectionTitle,
            section_id=request.sectionId,
            document_ids=document_ids,
            context_sections=request.contextSections if request.contextSections else None,
            custom_prompt=request.customPrompt if request.customPrompt else None
        )

        # 如果有当前段落，保存到版本历史
        if current_paragraph:
            # 将当前段落添加到版本历史
            existing_versions.append({
                "content": current_paragraph.get("content", ""),
                "timestamp": current_paragraph.get("timestamp", ""),
                "sources": current_paragraph.get("sources", [])
            })

        # 创建新段落（包含历史版本）
        updated_paragraph = {
            "paragraph_id": new_paragraph_data.get("paragraph_id"),
            "section_id": new_paragraph_data.get("section_id"),
            "content": new_paragraph_data.get("content"),
            "sources": new_paragraph_data.get("sources", []),
            "timestamp": new_paragraph_data.get("timestamp"),
            "versions": existing_versions  # 保存所有历史版本
        }

        # 更新项目（只保留一个段落，历史在versions中）
        document_project_storage.add_section_content(
            project_id=project_id,
            section_id=request.sectionId,
            content={
                "sectionId": request.sectionId,
                "paragraphs": [updated_paragraph],  # 只保留当前段落
                "sources": updated_paragraph.get("sources", [])
            }
        )

        return updated_paragraph

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"重新生成失败: {str(e)}")


@router.put("/{project_id}/paragraph")
async def update_paragraph(project_id: str, request: UpdateParagraphRequest):
    """
    更新段落内容（编辑）

    直接修改段落内容，不保存版本
    """
    try:
        updated_project = document_project_storage.update_paragraph(
            project_id=project_id,
            section_id=request.sectionId,
            paragraph_id=request.paragraphId,
            content=request.content,
            save_version=False  # 编辑时不保存版本
        )

        if not updated_project:
            raise HTTPException(status_code=404, detail="段落不存在")

        return {"message": "更新成功"}

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"更新失败: {str(e)}")


class RestoreParagraphVersionRequest(BaseModel):
    """恢复段落版本请求"""
    sectionId: str = Field(..., description="章节ID")
    paragraphId: str = Field(..., description="段落ID")
    versionIndex: int = Field(..., description="版本索引")


@router.post("/{project_id}/restore-paragraph-version")
async def restore_paragraph_version(project_id: str, request: RestoreParagraphVersionRequest):
    """
    恢复段落到指定版本

    将段落恢复到历史版本
    """
    try:
        updated_project = document_project_storage.restore_paragraph_version(
            project_id=project_id,
            section_id=request.sectionId,
            paragraph_id=request.paragraphId,
            version_index=request.versionIndex
        )

        if not updated_project:
            raise HTTPException(status_code=404, detail="段落或版本不存在")

        return updated_project

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"恢复失败: {str(e)}")


@router.get("/{project_id}/export-word")
async def export_word(project_id: str):
    """
    导出为 Word 文档

    将项目的大纲和内容导出为 Word 文档
    """
    try:
        project = document_project_storage.get_project(project_id)
        if not project:
            raise HTTPException(status_code=404, detail="项目不存在")

        # 创建 Word 文档
        doc = Document()

        # 小四号字体 = 12磅
        font_size_small4 = Pt(12)

        # 设置文档默认样式（Normal 样式）
        style = doc.styles['Normal']
        style.font.name = 'Times New Roman'
        style.font.size = font_size_small4
        # 设置中文字体
        style._element.rPr.rFonts.set(qn('w:eastAsia'), '宋体')

        # 设置文档标题
        title = project.get("title", "文档")
        title_heading = doc.add_heading(title, 0)
        title_heading.alignment = WD_ALIGN_PARAGRAPH.CENTER

        # 设置标题格式
        for run in title_heading.runs:
            run.font.size = font_size_small4
            run.font.bold = True
            run.font.color.rgb = RGBColor(0, 0, 0)
            run.font.underline = False
            # 使用 qn 设置字体
            run.font.name = 'Times New Roman'
            run._element.rPr.rFonts.set(qn('w:eastAsia'), '宋体')

        # 移除段落边框
        try:
            pPr = title_heading._element.get_or_add_pPr()
            pBdr = pPr.find(qn('w:pBdr'))
            if pBdr is not None:
                pPr.remove(pBdr)
        except:
            pass

        # 设置标题段后间距
        title_heading.paragraph_format.line_spacing = 1.5
        title_heading.paragraph_format.space_before = Pt(0)
        title_heading.paragraph_format.space_after = Pt(0)

        # 添加大纲内容
        outline = project.get("outline", [])
        sections = project.get("sections", {})

        def add_outline_to_doc(nodes: List, doc_level: int = 1):
            """递归添加大纲节点到 Word 文档"""
            for node in nodes:
                node_id = node.get("id")
                label = node.get("label", "无标题")

                # 添加章节标题
                heading = doc.add_heading(label, level=min(doc_level, 9))

                # 设置标题格式
                for run in heading.runs:
                    run.font.size = font_size_small4
                    run.font.bold = True
                    run.font.color.rgb = RGBColor(0, 0, 0)
                    run.font.underline = False
                    # 使用 qn 设置字体
                    run.font.name = 'Times New Roman'
                    run._element.rPr.rFonts.set(qn('w:eastAsia'), '宋体')

                # 移除段落边框
                try:
                    pPr = heading._element.get_or_add_pPr()
                    pBdr = pPr.find(qn('w:pBdr'))
                    if pBdr is not None:
                        pPr.remove(pBdr)
                except:
                    pass

                # 设置标题段后间距和行距
                heading.paragraph_format.line_spacing = 1.5
                heading.paragraph_format.space_before = Pt(0)
                heading.paragraph_format.space_after = Pt(0)

                # 添加章节内容（如果有）
                if node_id and node_id in sections:
                    section_data = sections[node_id]
                    paragraphs = section_data.get("paragraphs", [])

                    if paragraphs:
                        # 只显示最新段落（当前版本）
                        current_para = paragraphs[-1]
                        content = current_para.get("content", "")

                        if content.strip():
                            # 将内容按双换行符分割为多个段落
                            content_paragraphs = content.split('\n\n')

                            for para_text in content_paragraphs:
                                para_text = para_text.strip()
                                if not para_text:
                                    continue

                                # 添加段落
                                para = doc.add_paragraph(para_text)

                                # 设置段落两端对齐
                                para.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY

                                # 设置正文字体
                                for run in para.runs:
                                    run.font.size = font_size_small4
                                    # 使用 qn 设置字体
                                    run.font.name = 'Times New Roman'
                                    run._element.rPr.rFonts.set(qn('w:eastAsia'), '宋体')

                                # 设置段落格式：首行缩进两字符（约0.8厘米），行距1.5倍，段前段后0行
                                para.paragraph_format.first_line_indent = Inches(0.32)  # 首行缩进两字符
                                para.paragraph_format.line_spacing = 1.5  # 1.5倍行距
                                para.paragraph_format.space_before = Pt(0)  # 段前0行
                                para.paragraph_format.space_after = Pt(0)  # 段后0行

                # 递归处理子节点
                children = node.get("children", [])
                if children:
                    add_outline_to_doc(children, doc_level + 1)

        # 添加大纲内容
        if outline:
            add_outline_to_doc(outline)

        # 保存到内存
        file_stream = io.BytesIO()
        doc.save(file_stream)
        file_stream.seek(0)

        # 生成文件名（使用项目标题，URL 编码以支持中文）
        project_title = project.get("title", "文档")
        filename = f"{project_title}.docx"
        encoded_filename = quote(filename)

        # 返回文件流
        return StreamingResponse(
            file_stream,
            media_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
            headers={
                "Content-Disposition": f"attachment; filename*=UTF-8''{encoded_filename}"
            }
        )

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"导出失败: {str(e)}")


@router.get("/{project_id}/preview-html")
async def preview_html(project_id: str):
    """
    生成HTML预览

    生成项目内容的HTML预览，用于PDF导出
    """
    try:
        project = document_project_storage.get_project(project_id)
        if not project:
            raise HTTPException(status_code=404, detail="项目不存在")

        title = project.get("title", "文档")
        outline = project.get("outline", [])
        sections = project.get("sections", {})

        # 生成HTML
        html_content = f"""<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <title>{title}</title>
    <style>
        * {{
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }}

        @page {{
            size: A4;
            margin: 20mm;
        }}

        html, body {{
            margin: 0;
            padding: 0;
            width: 100%;
            height: 100%;
        }}

        body {{
            font-family: 'Times New Roman', '宋体', serif;
            font-size: 12pt;
            line-height: 1.5;
            max-width: 210mm;
            margin: 20mm auto;
            padding: 20mm;
            background: white;
        }}

        h1, h2, h3 {{
            font-size: 12pt;
            font-weight: bold;
            margin: 0;
            margin-top: 0;
            margin-bottom: 0;
            padding: 0;
            padding-top: 0;
            padding-bottom: 0;
            color: #000;
            line-height: 1.5;
            text-align: left;
        }}

        h1 {{
            text-align: center;
        }}

        p {{
            text-align: justify;
            text-indent: 2em;
            margin: 0;
            margin-top: 0;
            margin-bottom: 0;
            padding: 0;
            padding-top: 0;
            padding-bottom: 0;
            line-height: 1.5;
            font-size: 12pt;
            page-break-inside: avoid;
        }}

        @media print {{
            body {{
                margin: 0;
                padding: 20mm;
            }}

            h1, h2, h3, p {{
                margin: 0 !important;
                padding: 0 !important;
            }}
        }}
    </style>
</head>
<body>
    <h1>{title}</h1>
"""

        def add_outline_html(nodes: List, level: int = 1) -> str:
            """递归生成大纲HTML"""
            html = ""
            for node in nodes:
                node_id = node.get("id")
                label = node.get("label", "无标题")

                # 根据层级选择标题标签
                if level == 1:
                    html += f"<h2>{label}</h2>"
                elif level == 2:
                    html += f"<h3>{label}</h3>"
                else:
                    html += f"<h3>{label}</h3>"

                # 添加章节内容
                if node_id and node_id in sections:
                    section_data = sections[node_id]
                    paragraphs = section_data.get("paragraphs", [])

                    if paragraphs:
                        current_para = paragraphs[-1]
                        content = current_para.get("content", "")

                        if content.strip():
                            # 将双换行符分割为段落
                            content_paragraphs = content.split('\n\n')
                            for para_text in content_paragraphs:
                                para_text = para_text.strip()
                                if para_text:
                                    # 转义HTML特殊字符
                                    para_text = para_text.replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;')
                                    # 将换行符转为<br>
                                    para_text = para_text.replace('\n', '<br>')
                                    html += f"<p>{para_text}</p>"

                # 递归处理子节点
                children = node.get("children", [])
                if children:
                    html += add_outline_html(children, level + 1)

            return html

        if outline:
            html_content += add_outline_html(outline)

        html_content += """    <script>
        // 页面加载完成后自动触发打印对话框
        window.onload = function() {
            setTimeout(function() {
                window.print();
            }, 500);
        };
    </script>
</body>
</html>"""

        return HTMLResponse(content=html_content)

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"预览生成失败: {str(e)}")


