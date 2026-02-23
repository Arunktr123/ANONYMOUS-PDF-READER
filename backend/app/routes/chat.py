from fastapi import APIRouter, HTTPException, Header
from mysql.connector import Error
from typing import Optional
from app.database import get_db_connection
from app.schemas.schemas import ChatMessageCreate, ChatMessageResponse
from app.utils.helpers import verify_user_token

router = APIRouter(prefix="/api/chat", tags=["chat"])


@router.post("/{session_code}/send", response_model=ChatMessageResponse)
async def send_message(session_code: str, message: ChatMessageCreate, user_token: Optional[str] = Header(None, alias="x-user-token")):
    """Send a chat message"""
    connection = get_db_connection()
    cursor = connection.cursor(dictionary=True)
    
    try:
        # Verify user token
        if not verify_user_token(user_token):
            raise HTTPException(status_code=401, detail="Invalid user token")
        
        # Get session
        cursor.execute("SELECT id FROM sessions WHERE session_code = %s", (session_code,))
        session = cursor.fetchone()
        
        if not session:
            raise HTTPException(status_code=404, detail="Session not found")
        
        session_id = session["id"]
        
        # Get user
        cursor.execute("SELECT id FROM users WHERE user_token = %s", (user_token,))
        user = cursor.fetchone()
        
        if not user:
            raise HTTPException(status_code=401, detail="User not found")
        
        user_id = user["id"]
        
        # Insert message
        cursor.execute(
            """INSERT INTO chat_messages (session_id, user_id, pdf_id, message) 
               VALUES (%s, %s, %s, %s)""",
            (session_id, user_id, message.pdf_id, message.message)
        )
        connection.commit()
        
        message_id = cursor.lastrowid
        
        # Get the inserted message
        cursor.execute("SELECT * FROM chat_messages WHERE id = %s", (message_id,))
        saved_message = cursor.fetchone()
        
        return ChatMessageResponse(**saved_message)
    except Error as e:
        connection.rollback()
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        cursor.close()
        connection.close()


@router.get("/{session_code}/messages", response_model=list[ChatMessageResponse])
async def get_session_messages(session_code: str, user_token: Optional[str] = Header(None, alias="x-user-token"), limit: int = 100):
    """Get chat messages from a session"""
    connection = get_db_connection()
    cursor = connection.cursor(dictionary=True)
    
    try:
        # Verify user token
        if not verify_user_token(user_token):
            raise HTTPException(status_code=401, detail="Invalid user token")
        
        # Get session
        cursor.execute("SELECT id FROM sessions WHERE session_code = %s", (session_code,))
        session = cursor.fetchone()
        
        if not session:
            raise HTTPException(status_code=404, detail="Session not found")
        
        # Get messages
        cursor.execute(
            """SELECT * FROM chat_messages 
               WHERE session_id = %s 
               ORDER BY created_at DESC 
               LIMIT %s""",
            (session["id"], limit)
        )
        messages = cursor.fetchall()
        
        return list(reversed(messages))
    except Error as e:
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        cursor.close()
        connection.close()


@router.get("/{session_code}/pdf/{pdf_id}/messages", response_model=list[ChatMessageResponse])
async def get_pdf_messages(session_code: str, pdf_id: int, user_token: Optional[str] = Header(None, alias="user_token")):
    """Get chat messages for a specific PDF"""
    connection = get_db_connection()
    cursor = connection.cursor(dictionary=True)
    
    try:
        # Verify user token
        if not verify_user_token(user_token):
            raise HTTPException(status_code=401, detail="Invalid user token")
        
        # Get session
        cursor.execute("SELECT id FROM sessions WHERE session_code = %s", (session_code,))
        session = cursor.fetchone()
        
        if not session:
            raise HTTPException(status_code=404, detail="Session not found")
        
        # Get messages for specific PDF
        cursor.execute(
            """SELECT * FROM chat_messages 
               WHERE session_id = %s AND pdf_id = %s 
               ORDER BY created_at ASC""",
            (session["id"], pdf_id)
        )
        messages = cursor.fetchall()
        
        return messages
    except Error as e:
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        cursor.close()
        connection.close()
