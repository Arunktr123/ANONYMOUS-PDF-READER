from fastapi import APIRouter, HTTPException
from mysql.connector import Error
from app.database import get_db_connection
from app.schemas.schemas import SessionResponse, JoinSessionRequest, UserResponse
from app.utils.helpers import generate_session_code, generate_user_token, allocate_random_pdf
from datetime import datetime

router = APIRouter(prefix="/api/sessions", tags=["sessions"])


@router.post("/create", response_model=SessionResponse)
async def create_session():
    """Create a new session"""
    connection = get_db_connection()
    cursor = connection.cursor()
    
    try:
        session_code = generate_session_code()
        
        # Ensure unique session code
        while True:
            cursor.execute("SELECT id FROM sessions WHERE session_code = %s", (session_code,))
            if not cursor.fetchone():
                break
            session_code = generate_session_code()
        
        cursor.execute(
            "INSERT INTO sessions (session_code, is_active) VALUES (%s, TRUE)",
            (session_code,)
        )
        connection.commit()
        
        session_id = cursor.lastrowid
        
        return {
            "id": session_id,
            "session_code": session_code,
            "created_at": datetime.now(),
            "is_active": True
        }
    except Error as e:
        connection.rollback()
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        cursor.close()
        connection.close()


@router.post("/join", response_model=UserResponse)
async def join_session(request: JoinSessionRequest):
    """Join an existing session"""
    connection = get_db_connection()
    cursor = connection.cursor()
    
    try:
        # Get session by code
        cursor.execute("SELECT id FROM sessions WHERE session_code = %s AND is_active = TRUE", (request.session_code,))
        session = cursor.fetchone()
        
        if not session:
            raise HTTPException(status_code=404, detail="Session not found")
        
        session_id = session[0]
        user_token = generate_user_token()
        
        # Create user
        cursor.execute(
            "INSERT INTO users (session_id, user_token, is_active) VALUES (%s, %s, TRUE)",
            (session_id, user_token)
        )
        connection.commit()
        
        user_id = cursor.lastrowid
        
        # Allocate random PDF if available
        pdf_id = allocate_random_pdf(session_id, user_id, cursor)
        connection.commit()
        
        return {
            "id": user_id,
            "session_id": session_id,
            "user_token": user_token,
            "assigned_pdf_id": pdf_id
        }
    except Error as e:
        connection.rollback()
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        cursor.close()
        connection.close()


@router.get("/{session_code}")
async def get_session_info(session_code: str):
    """Get session information"""
    connection = get_db_connection()
    cursor = connection.cursor(dictionary=True)
    
    try:
        cursor.execute("SELECT * FROM sessions WHERE session_code = %s", (session_code,))
        session = cursor.fetchone()
        
        if not session:
            raise HTTPException(status_code=404, detail="Session not found")
        
        # Get active users count
        cursor.execute("SELECT COUNT(*) as count FROM users WHERE session_id = %s AND is_active = TRUE", (session["id"],))
        users_count = cursor.fetchone()["count"]
        
        # Get PDFs count
        cursor.execute("SELECT COUNT(*) as count FROM pdfs WHERE session_id = %s", (session["id"],))
        pdfs_count = cursor.fetchone()["count"]
        
        return {
            "session": session,
            "active_users": users_count,
            "total_pdfs": pdfs_count
        }
    except Error as e:
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        cursor.close()
        connection.close()
