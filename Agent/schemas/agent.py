from pydantic import BaseModel
from typing import Literal


class AgentQueryIn(BaseModel):
    query: str
    conversation_id: int
    uploaded_filename: str | None = None
    session_file_id: str | None = None


class AgentFileUploadOut(BaseModel):
    result: Literal["success", "failure"] = "success"
    message: str = "文件上传成功"
    filename: str
    conversation_id: int
    session_file_id: str
    chunk_count: int = 0
