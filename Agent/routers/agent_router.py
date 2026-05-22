from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile
from fastapi.responses import StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession

from agent_app.agent.react_agent import ReactAgent
from agent_app.rag.vector_store import VectorStoreService
from agent_app.utils.temp_file_service import get_temp_file_service
from core.auth import AuthHandler
from dependencies import get_session
from schemas.agent import AgentFileUploadOut, AgentQueryIn
from services.conversation_service import ConversationService

auth_handler = AuthHandler()

router = APIRouter(prefix="/agent", tags=["Agent"])

react_agent = ReactAgent()
vector_store_service = VectorStoreService()
temp_file_service = get_temp_file_service()


@router.post("/chat/stream")
async def chat_stream(
        payload: AgentQueryIn,
        user_id: int = Depends(auth_handler.auth_access_dependency),
        session: AsyncSession = Depends(get_session),
):
    svc = ConversationService(session)
    conv = await svc.get_conversation(payload.conversation_id, user_id)
    if not conv:
        raise HTTPException(status_code=404, detail="对话不存在")

    latest_file = await svc.get_latest_file(payload.conversation_id)
    uploaded_filename = latest_file.filename if latest_file else None
    session_file_id = latest_file.session_file_id if latest_file else None

    await svc.append_message(
        conversation_id=payload.conversation_id,
        role="user",
        content=payload.query,
        uploaded_filename=uploaded_filename,
        session_file_id=session_file_id,
    )

    async def generate():
        full_response = ""
        for chunk in react_agent.execute_stream(
            payload.query,
            payload.conversation_id,
            uploaded_filename,
            session_file_id,
        ):
            full_response += chunk
            yield chunk

        await svc.append_message(
            conversation_id=payload.conversation_id,
            role="agent",
            content=full_response,
        )

    return StreamingResponse(generate(), media_type="text/plain; charset=utf-8")


@router.post("/files/upload", response_model=AgentFileUploadOut)
async def upload_knowledge_file(
        file: UploadFile = File(...),
        conversation_id: int = Form(...),
        user_id: int = Depends(auth_handler.auth_access_dependency),
        session: AsyncSession = Depends(get_session),
):
    svc = ConversationService(session)
    conv = await svc.get_conversation(conversation_id, user_id)
    if not conv:
        raise HTTPException(status_code=404, detail="对话不存在")

    filename = (file.filename or "").strip()
    if not filename:
        raise HTTPException(status_code=400, detail="文件名不能为空")

    ext = filename.rsplit(".", 1)[-1].lower() if "." in filename else ""
    allowed_types = vector_store_service.get_allowed_types()
    if ext not in allowed_types:
        raise HTTPException(status_code=400, detail=f"仅支持上传：{', '.join(allowed_types)}")

    content = await file.read()
    if not content:
        raise HTTPException(status_code=400, detail="文件内容不能为空")

    try:
        session_file_id = temp_file_service.save_temp_file(conversation_id, content, filename)
        await svc.bind_file_to_conversation(conversation_id, session_file_id, filename)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"文件保存失败：{str(e)}")
    finally:
        await file.close()

    return AgentFileUploadOut(
        filename=filename,
        conversation_id=conversation_id,
        session_file_id=session_file_id,
        result="success",
        message="文件上传成功"
    )
