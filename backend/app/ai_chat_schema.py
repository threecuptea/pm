from typing import Literal

from pydantic import BaseModel, ConfigDict, Field

from backend.app.board_schema import BoardPayload


class ChatHistoryMessage(BaseModel):
    model_config = ConfigDict(extra="forbid")

    role: Literal["user", "assistant"]
    content: str = Field(min_length=1)


class AiChatRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    question: str = Field(min_length=1)
    history: list[ChatHistoryMessage] = []


class AiStructuredOutput(BaseModel):
    model_config = ConfigDict(extra="forbid")

    assistant_response: str = Field(min_length=1)
    board_update: BoardPayload | None = None


class AiChatResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    model: str
    assistant_response: str
    board_updated: bool
    board: BoardPayload
