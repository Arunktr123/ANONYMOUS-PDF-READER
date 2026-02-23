from fastapi import APIRouter, UploadFile, File, HTTPException, Header
from fastapi.responses import FileResponse
from mysql.connector import Error
import os
from typing import Optional
from app.database import get_db_connection
from app.config import settings
from app.schemas.schemas import PDFResponse
from app.utils.helpers import verify_user_token, allocate_random_pdf

router = APIRouter(prefix="/api/pdfs", tags=["pdfs"])


@router.post("/upload/{session_code}")
async def upload_pdf(session_code: str, file: UploadFile = File(...), user_token: Optional[str] = Header(None, alias="x-user-token")):
    """Upload a PDF to a session"""
    connection = get_db_connection()
    cursor = connection.cursor()
    
    try:
        # Verify user token
        if not verify_user_token(user_token):
            raise HTTPException(status_code=401, detail="Invalid user token")
        
        # Get session
        cursor.execute("SELECT id FROM sessions WHERE session_code = %s AND is_active = TRUE", (session_code,))
        session = cursor.fetchone()
        
        if not session:
            raise HTTPException(status_code=404, detail="Session not found")
        
        session_id = session[0]
        
        # Get user
        cursor.execute("SELECT id FROM users WHERE user_token = %s", (user_token,))
        user = cursor.fetchone()
        
        if not user:
            raise HTTPException(status_code=401, detail="User not found")
        
        user_id = user[0]
        
        # Check if user already uploaded a PDF in this session
        cursor.execute(
            "SELECT id FROM pdfs WHERE session_id = %s AND uploaded_by_user_id = %s",
            (session_id, user_id)
        )
        existing_pdf = cursor.fetchone()
        if existing_pdf:
            raise HTTPException(status_code=400, detail="You can only upload one PDF per session")
        
        # Save file
        os.makedirs(settings.UPLOAD_FOLDER, exist_ok=True)
        file_extension = os.path.splitext(file.filename)[1]
        saved_filename = f"{session_code}_{user_id}_{file.filename}"
        file_path = os.path.join(settings.UPLOAD_FOLDER, saved_filename)
        
        contents = await file.read()
        with open(file_path, "wb") as f:
            f.write(contents)
        
        # Save to database
        cursor.execute(
            """INSERT INTO pdfs (session_id, filename, file_path, uploaded_by_user_id, is_available) 
               VALUES (%s, %s, %s, %s, TRUE)""",
            (session_id, file.filename, saved_filename, user_id)
        )
        connection.commit()
        
        return {"message": "PDF uploaded successfully", "filename": file.filename}
    except Error as e:
        connection.rollback()
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        cursor.close()
        connection.close()


@router.get("/session/{session_code}", response_model=list[PDFResponse])
async def get_session_pdfs(session_code: str, user_token: Optional[str] = Header(None, alias="x-user-token")):
    """Get all PDFs in a session"""
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
        
        # Get PDFs
        cursor.execute(
            "SELECT id, session_id, filename, uploaded_at FROM pdfs WHERE session_id = %s",
            (session["id"],)
        )
        pdfs = cursor.fetchall()
        
        return pdfs
    except Error as e:
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        cursor.close()
        connection.close()


@router.get("/download/{pdf_id}")
async def download_pdf(pdf_id: int, user_token: Optional[str] = Header(None, alias="x-user-token")):
    """Download a PDF"""
    connection = get_db_connection()
    cursor = connection.cursor(dictionary=True)
    
    try:
        # Verify user token
        if not verify_user_token(user_token):
            raise HTTPException(status_code=401, detail="Invalid user token")
        
        # Get PDF
        cursor.execute("SELECT file_path, filename FROM pdfs WHERE id = %s", (pdf_id,))
        pdf = cursor.fetchone()
        
        if not pdf:
            raise HTTPException(status_code=404, detail="PDF not found")
        
        file_path = os.path.join(settings.UPLOAD_FOLDER, pdf["file_path"])
        
        if not os.path.exists(file_path):
            raise HTTPException(status_code=404, detail="File not found")
        
        return FileResponse(file_path, filename=pdf["filename"])
    except Error as e:
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        cursor.close()
        connection.close()


@router.post("/request-allocation/{session_code}")
async def request_pdf_allocation(session_code: str, user_token: Optional[str] = Header(None, alias="x-user-token")):
    """Request a random PDF to be assigned to the user"""
    connection = get_db_connection()
    cursor = connection.cursor(dictionary=True)
    
    try:
        # Verify user token
        if not verify_user_token(user_token):
            raise HTTPException(status_code=401, detail="Invalid user token")
        
        # Get session
        cursor.execute("SELECT id FROM sessions WHERE session_code = %s AND is_active = TRUE", (session_code,))
        session = cursor.fetchone()
        
        if not session:
            raise HTTPException(status_code=404, detail="Session not found")
        
        session_id = session["id"]
        
        # Get user
        cursor.execute("SELECT id, assigned_pdf_id FROM users WHERE user_token = %s", (user_token,))
        user = cursor.fetchone()
        
        if not user:
            raise HTTPException(status_code=401, detail="User not found")
        
        # Check if already has an assigned PDF
        if user["assigned_pdf_id"]:
            cursor.execute("SELECT id, filename FROM pdfs WHERE id = %s", (user["assigned_pdf_id"],))
            pdf = cursor.fetchone()
            return {"message": "PDF already assigned", "pdf": pdf}
        
        # Allocate random PDF (not their own)
        pdf_id = allocate_random_pdf(session_id, user["id"], cursor)
        connection.commit()
        
        if pdf_id:
            cursor.execute("SELECT id, filename FROM pdfs WHERE id = %s", (pdf_id,))
            pdf = cursor.fetchone()
            return {"message": "PDF assigned successfully", "pdf": pdf}
        else:
            return {"message": "No PDFs available yet", "pdf": None}
    except Error as e:
        connection.rollback()
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        cursor.close()
        connection.close()


@router.get("/my-assigned/{session_code}")
async def get_my_assigned_pdf(session_code: str, user_token: Optional[str] = Header(None, alias="x-user-token")):
    """Get the PDF assigned to the current user"""
    connection = get_db_connection()
    cursor = connection.cursor(dictionary=True)
    
    try:
        # Verify user token
        if not verify_user_token(user_token):
            raise HTTPException(status_code=401, detail="Invalid user token")
        
        # Get user with assigned PDF
        cursor.execute(
            """
            SELECT u.assigned_pdf_id, p.id, p.filename, p.uploaded_at
            FROM users u
            LEFT JOIN pdfs p ON u.assigned_pdf_id = p.id
            WHERE u.user_token = %s
            """,
            (user_token,)
        )
        result = cursor.fetchone()
        
        if not result:
            raise HTTPException(status_code=401, detail="User not found")
        
        if not result["assigned_pdf_id"]:
            return {"assigned": False, "pdf": None, "message": "No PDF assigned yet. Request allocation after PDFs are uploaded."}
        
        return {
            "assigned": True,
            "pdf": {
                "id": result["id"],
                "filename": result["filename"],
                "uploaded_at": result["uploaded_at"]
            }
        }
    except Error as e:
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        cursor.close()
        connection.close()
