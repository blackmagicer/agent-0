from fastapi import FastAPI
from fastapi_mail import FastMail, MessageSchema, MessageType
from fastapi import Depends
from routers.auth_router import router as auth_router
from routers.agent_router import router as agent_router
from routers.conversation_router import router as conversation_router
from dependencies import get_mail
from fastapi.middleware.cors import CORSMiddleware




app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth_router)
app.include_router(agent_router)
app.include_router(conversation_router)
@app.get("/")
async def root():
    return {"message": "Hello World"}


@app.get("/hello/{name}")
async def say_hello(name: str):
    return {"message": f"Hello {name}"}

@app.get("/mail/test")
async def mail_test(
        email: str,
        mail: FastMail = Depends(get_mail),
):
    message = MessageSchema(
        subject="hello",
        recipients=[email],
        body=f"hello {email}",
        subtype=MessageType.plain,
    )
    await mail.send_message(message)
    return {"message": "邮件发送成功！"}