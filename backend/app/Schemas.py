from pydantic import BaseModel, ConfigDict, Field, field_validator
from datetime import datetime

# パスワードの最小文字数
PASSWORD_MIN_CHARS = 4

# パスワードの最大文字数
PASSWORD_MAX_CHARS = 20

# ログインIDの最大文字数（Search.jsxの入力欄 maxLength と揃える）
USER_ID_MAX_CHARS = 30

# 定型文の最大文字数
TEMPLATE_MAX_CHARS = 100


# --- ユーザー関連 ---

class UserCreate(BaseModel):
    """POST /register のリクエスト（Register.jsxが送る3項目）"""

    model_config = ConfigDict(populate_by_name=True)

    user_id: str = Field(alias="id")  # ログインID
    username: str  # 画面に表示する名前
    password: str

    @field_validator("user_id")
    @classmethod
    def user_id_is_valid(cls, v: str) -> str:
        """ログインIDの形式を検証する"""
        if not v.strip():
            raise ValueError("IDを入力してください")
        if any(c.isspace() for c in v):
            raise ValueError("IDに空白は使用できません")
        if len(v) > USER_ID_MAX_CHARS:
            raise ValueError(f"IDは{USER_ID_MAX_CHARS}文字以内にしてください")
        return v

    @field_validator("username")
    @classmethod
    def username_not_empty(cls, v: str) -> str:
        if not v.strip():
            raise ValueError("ユーザーネームを入力してください")
        return v.strip()

    @field_validator("password")
    @classmethod
    def password_within_limit(cls, v: str) -> str:
        """パスワードの文字数下限とbcryptのバイト数上限を検証する"""
        if len(v) < PASSWORD_MIN_CHARS:
            raise ValueError(f"パスワードは{PASSWORD_MIN_CHARS}文字以上にしてください")
        if len(v) > PASSWORD_MAX_CHARS:
            raise ValueError(f"パスワードは{PASSWORD_MAX_CHARS}文字以内にしてください")
        return v


class UserLogin(BaseModel):
    """POST /login のリクエスト"""

    model_config = ConfigDict(populate_by_name=True)

    user_id: str = Field(alias="id")
    password: str


class UserResponse(BaseModel):
    """ユーザー情報のレスポンス

    ログインIDと表示名だけを返す。
    """

    model_config = ConfigDict(from_attributes=True)

    user_id: str
    username: str


# --- フォロー関連 ---
class FollowedUserResponse(BaseModel):
    """GET /follows のレスポンス1件（Inbox.jsxが読むキー）"""

    model_config = ConfigDict(from_attributes=True)

    user_id: str
    username: str
    # Trueで既読。
    read_status: bool
    # 相手の最新メッセージ。1件もなければNone
    latest_message: str | None


# --- 投稿関連 ---
class PostCreate(BaseModel):
    content: str


class PostResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    content: str
    created_at: datetime
    author: UserResponse


# --- 定型文関連 ---
class TemplateCreate(BaseModel):
    """定型文の登録・更新リクエスト"""

    content: str

    @field_validator("content")
    @classmethod
    def content_within_limit(cls, v: str) -> str:
        stripped = v.strip()
        if not stripped:
            raise ValueError("定型文を入力してください")
        if len(stripped) > TEMPLATE_MAX_CHARS:
            raise ValueError(f"定型文は{TEMPLATE_MAX_CHARS}文字以内にしてください")
        return stripped


class TemplateResponse(BaseModel):

    model_config = ConfigDict(from_attributes=True)

    id: int
    content: str
