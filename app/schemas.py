from typing import Optional, List, Literal
from pydantic import BaseModel, EmailStr, Field

class ChatRequest(BaseModel):
    session_id: Optional[str] = None
    message: str


class ChatResponse(BaseModel):
    session_id: str
    reply: str
    ended: bool = False


class Message(BaseModel):
    role: Literal["user", "assistant"]
    content: str


class TranscriptResponse(BaseModel):
    session_id: str
    messages: List[Message]
    ended: bool


class Analytics(BaseModel):
    session_id: str
    language_used: str
    configuration_interest: Optional[str] = None
    budget_signal: Optional[str] = None
    timeline: Optional[str] = None
    purpose: Optional[str] = None
    interest_level: Literal["hot", "warm", "cold", "unknown"] = "unknown"
    objections_raised: List[str] = []
    site_visit_status: Literal["booked", "failed", "proposed", "not_discussed"] = "not_discussed"
    site_visit_datetime: Optional[str] = None
    escalated_to_human: bool = False
    do_not_contact: bool = False
    follow_up_required: bool = False
    follow_up_note: Optional[str] = None
    summary: str = ""

class UserSignup(BaseModel):
    username: str = Field(..., min_length=3, max_length=50)
    password: str = Field(..., min_length=6)
    email: EmailStr | None = None


class UserLogin(BaseModel):
    username: str
    password: str


class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"