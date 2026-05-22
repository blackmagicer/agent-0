from datetime import datetime
from typing import Literal

from pydantic import BaseModel


class CreateConversationIn(BaseModel):
    title: str | None = None


class ConversationOut(BaseModel):
    id: int
    title: str
    created_at: datetime
    updated_at: datetime


class ConversationListOut(BaseModel):
    items: list[ConversationOut]
    total: int


class MessageOut(BaseModel):
    id: int
    role: str
    content: str
    uploaded_filename: str | None = None
    session_file_id: str | None = None
    created_at: datetime


class CreateConversationOut(BaseModel):
    id: int
    title: str


class DeleteConversationOut(BaseModel):
    result: Literal["success", "failure"] = "success"
    deleted_file_count: int = 0
