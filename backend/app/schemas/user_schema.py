import re
from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field, field_validator


ALPHANUMERIC = re.compile(r"^[A-Za-z0-9]+$")


class UserCreate(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    user_id: str = Field(alias="id", min_length=6, max_length=30)
    username: str = Field(min_length=1, max_length=100)
    password: str = Field(min_length=6, max_length=72)

    @field_validator("user_id", "password")
    @classmethod
    def validate_credentials(cls, value: str) -> str:
        if not ALPHANUMERIC.fullmatch(value):
            raise ValueError("英字と数字のみ使用できます")
        return value

    @field_validator("username")
    @classmethod
    def validate_name(cls, value: str) -> str:
        value = value.strip()
        if not value:
            raise ValueError("名前を入力してください")
        return value


class UserLogin(BaseModel):
    model_config = ConfigDict(populate_by_name=True)
    user_id: str = Field(alias="id")
    password: str


class UserResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    user_id: str
    username: str


class AuthResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: UserResponse


class UserSearchResponse(UserResponse):
    follow_status: str


class FriendResponse(UserResponse):
    read_status: bool = True
    latest_message: str | None = None
    latest_message_at: datetime | None = None


class FriendRequestResponse(BaseModel):
    id: int
    sender: UserResponse
    created_at: datetime


class AccountResponse(UserResponse):
    friend_count: int
