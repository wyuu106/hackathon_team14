from pydantic import BaseModel, EmailStr, field_validator
from datetime import datetime

# パスワードの最小文字数
PASSWORD_MIN_CHARS = 4

# パスワードの最大文字数
PASSWORD_MAX_CHARS = 20

# --- ユーザー関連 ---
class UserCreate(BaseModel):
    username: str
    email: EmailStr
    password: str

    @field_validator("password")
    @classmethod
    def password_within_limit(cls, v: str) -> str:
        """パスワードの文字数下限とbcryptのバイト数上限を検証する"""
        if len(v) < PASSWORD_MIN_CHARS:
            raise ValueError(
                f"パスワードは{PASSWORD_MIN_CHARS}文字以上にしてください"
            )
        if len(v) > PASSWORD_MAX_CHARS:
            raise ValueError(
                f"パスワードは{PASSWORD_MAX_CHARS}文字以内にしてください"
            )
        return v

class UserResponse(BaseModel):
    id: int
    username: str
    email: str

    class Config:
        from_attributes = True

# --- 投稿関連 ---
class PostCreate(BaseModel):
    content: str

class PostResponse(BaseModel):
    id: int
    content: str
    user_id: int
    created_at: datetime
    author: UserResponse

    class Config:
        from_attributes = True