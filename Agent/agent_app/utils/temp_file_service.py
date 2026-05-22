"""
临时会话文件服务：管理上传到临时目录的文件，按 conversation_id + session_file_id 存储与读取，
不写入长期知识库（Chroma / md5_store）。
"""
from __future__ import annotations

import os
import uuid
from typing import Optional

from agent_app.utils.file_handler import pdf_loader, txt_loader
from agent_app.utils.logger_handler import logger
from agent_app.utils.path_tool import get_abs_path


class TempFileService:
    TEMP_DIR_NAME = "temp_uploads"

    def __init__(self, temp_dir: Optional[str] = None):
        self.temp_dir = temp_dir or get_abs_path(self.TEMP_DIR_NAME)
        os.makedirs(self.temp_dir, exist_ok=True)

    def _get_file_path(self, conversation_id: int, session_file_id: str, filename: str) -> str:
        """根据 conversation_id、session_file_id 和原始文件名构造存储路径。"""
        safe_filename = os.path.basename(filename)
        return os.path.join(self.temp_dir, f"{conversation_id}_{session_file_id}_{safe_filename}")

    def save_temp_file(self, conversation_id: int, content: bytes, filename: str) -> str:
        """将上传内容直接写入临时目录并返回生成的 session_file_id。"""
        session_file_id = str(uuid.uuid4())
        dest_path = self._get_file_path(conversation_id, session_file_id, filename)

        with open(dest_path, "wb") as f:
            f.write(content)

        logger.info(f"[TempFileService] 文件已保存为临时文件: {conversation_id}/{session_file_id}, 路径: {dest_path}")
        return session_file_id

    def get_file_path(self, conversation_id: int, session_file_id: str, filename: str) -> Optional[str]:
        """根据 conversation_id、session_file_id 和文件名查找已存储的临时文件路径。"""
        path = self._get_file_path(conversation_id, session_file_id, filename)
        if os.path.exists(path):
            return path
        return None

    def read_file_content(self, conversation_id: int, session_file_id: str, filename: str, max_chars: int = 15000) -> str:
        """
        读取临时文件内容并截取前 max_chars 个字符（防止上下文过长）。
        返回文件文本内容。
        """
        path = self.get_file_path(conversation_id, session_file_id, filename)
        if not path:
            return f"文件 {filename} 未找到（可能已过期或不存在）"

        ext = (filename or "").rsplit(".", 1)[-1].lower()
        try:
            if ext == "txt":
                documents = txt_loader(path)
            elif ext == "pdf":
                documents = pdf_loader(path)
            else:
                return f"不支持的文件类型: {ext}"

            if not documents:
                return "文件内容为空"

            full_text = "\n".join(doc.page_content for doc in documents)
            if len(full_text) > max_chars:
                return full_text[:max_chars] + f"\n...（已截断，原文约 {len(full_text)} 字）"
            return full_text
        except Exception as e:
            logger.error(f"[TempFileService] 读取文件失败: {conversation_id}/{session_file_id}/{filename} -> {str(e)}")
            return f"文件读取失败: {str(e)}"

    def delete_file(self, conversation_id: int, session_file_id: str, filename: str) -> bool:
        """删除指定的临时文件。"""
        path = self.get_file_path(conversation_id, session_file_id, filename)
        if path and os.path.exists(path):
            try:
                os.remove(path)
                logger.info(f"[TempFileService] 已删除临时文件: {conversation_id}/{session_file_id}/{filename}")
                return True
            except Exception as e:
                logger.error(f"[TempFileService] 删除文件失败: {str(e)}")
        return False

    def list_conversation_files(self, conversation_id: int) -> list[tuple[str, str]]:
        files: list[tuple[str, str]] = []
        prefix = f"{conversation_id}_"
        for fname in os.listdir(self.temp_dir):
            if not fname.startswith(prefix):
                continue
            parts = fname.split("_", 2)
            if len(parts) != 3:
                continue
            _, session_file_id, filename = parts
            files.append((session_file_id, filename))
        return files

    def cleanup_expired(self, max_age_seconds: int = 3600 * 24):
        """删除超过 max_age_seconds 的临时文件（默认 24 小时）。"""
        import time

        now = time.time()
        cleaned = 0
        for fname in os.listdir(self.temp_dir):
            fpath = os.path.join(self.temp_dir, fname)
            if os.path.isfile(fpath) and now - os.path.getmtime(fpath) > max_age_seconds:
                try:
                    os.remove(fpath)
                    cleaned += 1
                except Exception:
                    pass
        logger.info(f"[TempFileService] 清理了 {cleaned} 个过期临时文件")


_temp_file_service: Optional[TempFileService] = None


def get_temp_file_service() -> TempFileService:
    global _temp_file_service
    if _temp_file_service is None:
        _temp_file_service = TempFileService()
    return _temp_file_service
