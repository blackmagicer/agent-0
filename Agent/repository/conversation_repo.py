from datetime import datetime

from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession

from models.conversation import Conversation, ConversationFile, Message


class ConversationRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def create(self, user_id: int, title: str = "新对话") -> Conversation:
        async with self.session.begin():
            conversation = Conversation(user_id=user_id, title=title)
            self.session.add(conversation)
        return conversation

    async def get_by_user(self, user_id: int) -> list[Conversation]:
        async with self.session.begin():
            stmt = select(Conversation).where(Conversation.user_id == user_id).order_by(Conversation.updated_at.desc())
            result = await self.session.scalars(stmt)
            return list(result)

    async def get_by_id(self, conversation_id: int, user_id: int) -> Conversation | None:
        async with self.session.begin():
            stmt = select(Conversation).where(
                Conversation.id == conversation_id,
                Conversation.user_id == user_id,
            )
            return await self.session.scalar(stmt)

    async def get_any_by_id(self, conversation_id: int) -> Conversation | None:
        async with self.session.begin():
            stmt = select(Conversation).where(Conversation.id == conversation_id)
            return await self.session.scalar(stmt)

    async def update_title(self, conversation: Conversation, title: str) -> Conversation:
        async with self.session.begin():
            conversation.title = title
            conversation.updated_at = datetime.now()
            self.session.add(conversation)
        return conversation

    async def touch(self, conversation: Conversation) -> Conversation:
        async with self.session.begin():
            conversation.updated_at = datetime.now()
            self.session.add(conversation)
        return conversation

    async def delete(self, conversation: Conversation) -> None:
        async with self.session.begin():
            await self.session.delete(conversation)


class MessageRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def create(
        self,
        conversation_id: int,
        role: str,
        content: str,
        uploaded_filename: str | None = None,
        session_file_id: str | None = None,
    ) -> Message:
        async with self.session.begin():
            message = Message(
                conversation_id=conversation_id,
                role=role,
                content=content,
                uploaded_filename=uploaded_filename,
                session_file_id=session_file_id,
            )
            self.session.add(message)
        return message

    async def get_by_conversation(self, conversation_id: int) -> list[Message]:
        async with self.session.begin():
            stmt = select(Message).where(Message.conversation_id == conversation_id).order_by(Message.created_at.asc())
            result = await self.session.scalars(stmt)
            return list(result)

    async def delete_by_conversation(self, conversation_id: int) -> None:
        async with self.session.begin():
            await self.session.execute(delete(Message).where(Message.conversation_id == conversation_id))


class ConversationFileRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def create(self, conversation_id: int, session_file_id: str, filename: str) -> ConversationFile:
        async with self.session.begin():
            conversation_file = ConversationFile(
                conversation_id=conversation_id,
                session_file_id=session_file_id,
                filename=filename,
            )
            self.session.add(conversation_file)
        return conversation_file

    async def get_by_conversation(self, conversation_id: int) -> list[ConversationFile]:
        async with self.session.begin():
            stmt = select(ConversationFile).where(ConversationFile.conversation_id == conversation_id).order_by(ConversationFile.created_at.asc())
            result = await self.session.scalars(stmt)
            return list(result)

    async def get_latest_by_conversation(self, conversation_id: int) -> ConversationFile | None:
        async with self.session.begin():
            stmt = (
                select(ConversationFile)
                .where(ConversationFile.conversation_id == conversation_id)
                .order_by(ConversationFile.created_at.desc())
                .limit(1)
            )
            return await self.session.scalar(stmt)

    async def delete_by_conversation(self, conversation_id: int) -> None:
        async with self.session.begin():
            await self.session.execute(delete(ConversationFile).where(ConversationFile.conversation_id == conversation_id))
