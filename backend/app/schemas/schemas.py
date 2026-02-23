from pydantic import BaseModel
from typing import Optional
from datetime import datetime


class SessionCreate(BaseModel):
    pass


class SessionResponse(BaseModel):
    id: int
    session_code: str
    created_at: datetime
    is_active: bool


class UserResponse(BaseModel):
    id: int
    session_id: int
    user_token: str
    assigned_pdf_id: Optional[int] = None


class PDFResponse(BaseModel):
    id: int
    session_id: int
    filename: str
    uploaded_at: datetime


class PDFUpload(BaseModel):
    filename: str


class ChatMessageCreate(BaseModel):
    message: str
    pdf_id: Optional[int] = None


class ChatMessageResponse(BaseModel):
    id: int
    session_id: int
    user_id: int
    pdf_id: Optional[int]
    message: str
    created_at: datetime


class JoinSessionRequest(BaseModel):
    session_code: str
