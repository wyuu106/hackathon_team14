from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field, field_validator

from .user_schema import UserResponse


class ChatCreate(BaseModel):
    content: str = Field(min_length=1, max_length=1000)

    @field_validator("content")
    @classmethod
    def strip_content(cls, value: str) -> str:
        value = value.strip()
        if not value:
            raise ValueError("メッセージを入力してください")
        return value


class ChatResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    content: str
    created_at: datetime
    author: UserResponse


class MessageItem(BaseModel):
    message_id: int
    content: str
    created_at: datetime


class MessageHistoryResponse(BaseModel):
    user_id: str
    username: str
    is_own: bool
    messages: list[MessageItem]


class MessageViewerResponse(UserResponse):
    read_at: datetime


class TemplateCreate(BaseModel):
    content: str = Field(min_length=1, max_length=100)

    @field_validator("content")
    @classmethod
    def strip_content(cls, value: str) -> str:
        value = value.strip()
        if not value:
            raise ValueError("定型文を入力してください")
        return value


class TemplateResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    content: str


class TemplateReorder(BaseModel):
    template_ids: list[int] = Field(min_length=1)
