from typing import Optional
from datetime import datetime


class Session:
    def __init__(self, id: int, session_code: str, created_at: datetime, is_active: bool):
        self.id = id
        self.session_code = session_code
        self.created_at = created_at
        self.is_active = is_active


class User:
    def __init__(self, id: int, session_id: int, user_token: str, assigned_pdf_id: Optional[int] = None):
        self.id = id
        self.session_id = session_id
        self.user_token = user_token
        self.assigned_pdf_id = assigned_pdf_id


class PDF:
    def __init__(self, id: int, session_id: int, filename: str, file_path: str, uploaded_at: datetime):
        self.id = id
        self.session_id = session_id
        self.filename = filename
        self.file_path = file_path
        self.uploaded_at = uploaded_at


class ChatMessage:
    def __init__(self, id: int, session_id: int, user_id: int, message: str, pdf_id: Optional[int] = None, created_at: Optional[datetime] = None):
        self.id = id
        self.session_id = session_id
        self.user_id = user_id
        self.pdf_id = pdf_id
        self.message = message
        self.created_at = created_at or datetime.now()
