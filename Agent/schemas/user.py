from pydantic import BaseModel, EmailStr, Field, model_validator
from typing import Annotated


UsernameStr = Annotated[str, Field(min_length=3, max_length=20, description="用户名")]
PasswordStr = Annotated[str, Field(min_length=6, max_length=20, description="密码")]

class RegisterIn(BaseModel):
    email: EmailStr
    username: UsernameStr
    password: PasswordStr
    confirm_password: PasswordStr
    code: Annotated[str, Field(min_length=4, max_length=4, description="邮箱验证码")]

    @model_validator(mode="after")
    def password_is_math(self):
        if self.password != self.confirm_password:
            raise ValueError("两个密码不一致！")
        return self


class UserCreateSchema(BaseModel):
    email: EmailStr
    username: UsernameStr
    password: PasswordStr


class LoginIn(BaseModel):
    email: EmailStr
    password: PasswordStr


class UserSchema(BaseModel):
    id: Annotated[int, Field(...)]
    email: EmailStr
    username: UsernameStr


class LoginOut(BaseModel):
    user: UserSchema
    token: str
