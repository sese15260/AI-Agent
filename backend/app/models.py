from datetime import date
from pydantic import BaseModel, ConfigDict, Field, field_validator


class DataIn(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True)
    date: date
    value: float = Field(gt=0, description="종가, 원")
    memo: str = Field(default="", max_length=300)


class DataOut(DataIn):
    id: str


class Message(BaseModel):
    role: str
    content: str = Field(min_length=1, max_length=4000)

    @field_validator("role")
    @classmethod
    def valid_role(cls, value):
        if value not in {"user", "assistant"}:
            raise ValueError("role must be user or assistant")
        return value


class ConversationIn(BaseModel):
    title: str = Field(min_length=1, max_length=100)
    messages: list[Message] = Field(min_length=1, max_length=50)


class ChatIn(BaseModel):
    message: str = Field(min_length=1, max_length=2000)
    conversation_id: str | None = None
