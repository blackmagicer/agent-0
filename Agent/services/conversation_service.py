"""
Conversation service: orchestrates conversation/message/file persistence
and delegates temp file cleanup to TempFileService.
"""
from sqlalchemy.ext.asyncio import AsyncSession

from agent_app.utils.temp_file_service import get_temp_file_service
from models.conversation import Conversation
from repository.conversation_repo import ConversationFileRepository, ConversationRepository, MessageRepository
from schemas.conversation import ConversationListOut, ConversationOut, CreateConversationOut, MessageOut


class ConversationService:
    def __init__(self, session: AsyncSession):
        self.session = session
        self.conv_repo = ConversationRepository(session)
        self.msg_repo = MessageRepository(session)
        self.file_repo = ConversationFileRepository(session)
        self.temp_file_service = get_temp_file_service()

    # ── Conversation ────────────────────────────────────────────────────────────

    async def create_conversation(self, user_id: int, title: str | None = None) -> CreateConversationOut:
        conv = await self.conv_repo.create(user_id, title or "新对话")
        return CreateConversationOut(id=conv.id, title=conv.title)

    async def list_conversations(self, user_id: int) -> ConversationListOut:
        conversations = await self.conv_repo.get_by_user(user_id)
        items = [
            ConversationOut(
                id=c.id,
                title=c.title,
                created_at=c.created_at,
                updated_at=c.updated_at,
            )
            for c in conversations
        ]
        return ConversationListOut(items=items, total=len(items))

    async def get_conversation(self, conversation_id: int, user_id: int) -> Conversation | None:
        return await self.conv_repo.get_by_id(conversation_id, user_id)

    async def update_conversation_title(self, conversation_id: int, user_id: int, title: str) -> None:
        conv = await self.conv_repo.get_by_id(conversation_id, user_id)
        if conv:
            await self.conv_repo.update_title(conv, title)

    async def delete_conversation(self, conversation_id: int, user_id: int) -> int:
        conv = await self.conv_repo.get_by_id(conversation_id, user_id)
        if not conv:
            return 0

        files = await self.file_repo.get_by_conversation(conversation_id)
        file_count = len(files)

        await self.conv_repo.delete(conv)

        for f in files:
            self.temp_file_service.delete_file(conversation_id, f.session_file_id, f.filename)

        return file_count

    # ── Messages ───────────────────────────────────────────────────────────────

    async def append_message(
        self,
        conversation_id: int,
        role: str,
        content: str,
        uploaded_filename: str | None = None,
        session_file_id: str | None = None,
    ) -> MessageOut:
        msg = await self.msg_repo.create(
            conversation_id=conversation_id,
            role=role,
            content=content,
            uploaded_filename=uploaded_filename,
            session_file_id=session_file_id,
        )
        conv = await self.conv_repo.get_any_by_id(conversation_id)
        if conv:
            await self.conv_repo.touch(conv)
        return MessageOut(
            id=msg.id,
            role=msg.role,
            content=msg.content,
            uploaded_filename=msg.uploaded_filename,
            session_file_id=msg.session_file_id,
            created_at=msg.created_at,
        )

    async def get_messages(self, conversation_id: int) -> list[MessageOut]:
        messages = await self.msg_repo.get_by_conversation(conversation_id)
        return [
            MessageOut(
                id=m.id,
                role=m.role,
                content=m.content,
                uploaded_filename=m.uploaded_filename,
                session_file_id=m.session_file_id,
                created_at=m.created_at,
            )
            for m in messages
        ]

    # ── Conversation Files ─────────────────────────────────────────────────────

    async def bind_file_to_conversation(
        self,
        conversation_id: int,
        session_file_id: str,
        filename: str,
    ) -> None:
        await self.file_repo.create(conversation_id, session_file_id, filename)
        conv = await self.conv_repo.get_any_by_id(conversation_id)
        if conv:
            await self.conv_repo.touch(conv)

    async def get_conversation_files(self, conversation_id: int) -> list:
        return await self.file_repo.get_by_conversation(conversation_id)

    async def get_latest_file(self, conversation_id: int):
        return await self.file_repo.get_latest_by_conversation(conversation_id)