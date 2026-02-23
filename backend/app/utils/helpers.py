import string
import random
import jwt
from datetime import datetime, timedelta
from app.config import settings


def generate_session_code(length: int = 8) -> str:
    """Generate a unique session code"""
    characters = string.ascii_uppercase + string.digits
    return ''.join(random.choices(characters, k=length))


def generate_user_token() -> str:
    """Generate a unique user token"""
    return jwt.encode(
        {
            "exp": datetime.utcnow() + timedelta(days=7),
            "iat": datetime.utcnow(),
            "data": random.randint(1000000, 9999999)
        },
        settings.SECRET_KEY,
        algorithm=settings.ALGORITHM
    )


def verify_user_token(token: str) -> bool:
    """Verify a user token"""
    if not token:
        return False
    try:
        jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        return True
    except:
        return False


def allocate_random_pdf(session_id: int, user_id: int, cursor):
    """Randomly allocate a PDF to a user in a session (not their own PDF)"""
    try:
        # Get a random PDF that:
        # 1. Belongs to this session
        # 2. Is available
        # 3. Was NOT uploaded by this user (anonymous exchange)
        cursor.execute(
            """
            SELECT id FROM pdfs 
            WHERE session_id = %s 
              AND is_available = TRUE 
              AND (uploaded_by_user_id IS NULL OR uploaded_by_user_id != %s)
            ORDER BY RAND() LIMIT 1
            """,
            (session_id, user_id)
        )
        result = cursor.fetchone()
        
        if result:
            pdf_id = result[0] if isinstance(result, tuple) else result.get('id')
            cursor.execute(
                "UPDATE users SET assigned_pdf_id = %s WHERE id = %s",
                (pdf_id, user_id)
            )
            return pdf_id
        return None
    except Exception as e:
        print(f"Error allocating PDF: {e}")
        return None
