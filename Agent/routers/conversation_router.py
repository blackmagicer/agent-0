"""
Conversation router: CRUD for conversations, messages, and file bindings.
"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from core.auth import AuthHandler
from dependencies import get_session
from schemas.conversation import (
    ConversationListOut,
    ConversationOut,
    CreateConversationIn,
    CreateConversationOut,
    DeleteConversationOut,
    MessageOut,
)
from schemas import ResponseOut
from services.conversation_service import ConversationService

auth_handler = AuthHandler()
router = APIRouter(prefix="/agent/conversations", tags=["Conversation"])


def get_conversation_service(session: AsyncSession = Depends(get_session)) -> ConversationService:
    return ConversationService(session)


# ── Conversation CRUD ─────────────────────────────────────────────────────────

@router.get("", response_model=ConversationListOut)
async def list_conversations(
    user_id: int = Depends(auth_handler.auth_access_dependency),
    svc: ConversationService = Depends(get_conversation_service),
):
    """List all conversations for the authenticated user."""
    return await svc.list_conversations(user_id)


@router.post("", response_model=CreateConversationOut)
async def create_conversation(
    payload: CreateConversationIn | None = None,
    user_id: int = Depends(auth_handler.auth_access_dependency),
    svc: ConversationService = Depends(get_conversation_service),
):
    """Create a new conversation."""
    title = payload.title if payload else None
    return await svc.create_conversation(user_id, title)


@router.get("/{conversation_id}", response_model=ConversationOut)
async def get_conversation(
    conversation_id: int,
    user_id: int = Depends(auth_handler.auth_access_dependency),
    svc: ConversationService = Depends(get_conversation_service),
):
    """Get a single conversation metadata."""
    conv = await svc.get_conversation(conversation_id, user_id)
    if not conv:
        raise HTTPException(status_code=404, detail="对话不存在")
    return ConversationOut(id=conv.id, title=conv.title, created_at=conv.created_at, updated_at=conv.updated_at)


@router.patch("/{conversation_id}", response_model=ResponseOut)
async def update_conversation_title(
    conversation_id: int,
    payload: CreateConversationIn,
    user_id: int = Depends(auth_handler.auth_access_dependency),
    svc: ConversationService = Depends(get_conversation_service),
):
    """Update conversation title (typically after first message)."""
    if not payload.title:
        raise HTTPException(status_code=400, detail="标题不能为空")
    conv = await svc.get_conversation(conversation_id, user_id)
    if not conv:
        raise HTTPException(status_code=404, detail="对话不存在")
    await svc.update_conversation_title(conversation_id, user_id, payload.title)
    return ResponseOut(result="success")


@router.delete("/{conversation_id}", response_model=DeleteConversationOut)
async def delete_conversation(
    conversation_id: int,
    user_id: int = Depends(auth_handler.auth_access_dependency),
    svc: ConversationService = Depends(get_conversation_service),
):
    """Delete a conversation and its associated temp files."""
    deleted_count = await svc.delete_conversation(conversation_id, user_id)
    return DeleteConversationOut(result="success", deleted_file_count=deleted_count)


# ── Messages ──────────────────────────────────────────────────────────────────

@router.get("/{conversation_id}/messages", response_model=list[MessageOut])
async def get_messages(
    conversation_id: int,
    user_id: int = Depends(auth_handler.auth_access_dependency),
    svc: ConversationService = Depends(get_conversation_service),
):
    """Get all messages for a conversation (for history restore)."""
    conv = await svc.get_conversation(conversation_id, user_id)
    if not conv:
        raise HTTPException(status_code=404, detail="对话不存在")
    return await svc.get_messages(conversation_id)