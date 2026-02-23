import mysql.connector
from mysql.connector import Error
from app.config import settings


def create_database_if_not_exists():
    """Create the database if it doesn't exist"""
    try:
        connection = mysql.connector.connect(
            host=settings.DATABASE_HOST,
            user=settings.DATABASE_USER,
            password=settings.DATABASE_PASSWORD,
            port=settings.DATABASE_PORT
        )
        cursor = connection.cursor()
        cursor.execute(f"CREATE DATABASE IF NOT EXISTS {settings.DATABASE_DB}")
        connection.commit()
        cursor.close()
        connection.close()
        print(f"Database '{settings.DATABASE_DB}' ready")
    except Error as e:
        print(f"Error creating database: {e}")
        raise


def get_db_connection():
    """Create and return a database connection"""
    try:
        connection = mysql.connector.connect(
            host=settings.DATABASE_HOST,
            user=settings.DATABASE_USER,
            password=settings.DATABASE_PASSWORD,
            database=settings.DATABASE_DB,
            port=settings.DATABASE_PORT
        )
        return connection
    except Error as e:
        print(f"Error connecting to MySQL: {e}")
        raise


def init_db():
    """Initialize database tables"""
    create_database_if_not_exists()
    connection = get_db_connection()
    cursor = connection.cursor()
    
    try:
        # Create sessions table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS sessions (
                id INT AUTO_INCREMENT PRIMARY KEY,
                session_code VARCHAR(20) UNIQUE NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                is_active BOOLEAN DEFAULT TRUE,
                expires_at TIMESTAMP
            )
        """)
        
        # Create users table (anonymous users in sessions)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS users (
                id INT AUTO_INCREMENT PRIMARY KEY,
                session_id INT NOT NULL,
                user_token VARCHAR(255) UNIQUE NOT NULL,
                assigned_pdf_id INT,
                joined_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                is_active BOOLEAN DEFAULT TRUE,
                FOREIGN KEY (session_id) REFERENCES sessions(id) ON DELETE CASCADE
            )
        """)
        
        # Create PDFs table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS pdfs (
                id INT AUTO_INCREMENT PRIMARY KEY,
                session_id INT NOT NULL,
                filename VARCHAR(255) NOT NULL,
                file_path VARCHAR(500) NOT NULL,
                uploaded_by_user_id INT,
                uploaded_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                is_available BOOLEAN DEFAULT TRUE,
                FOREIGN KEY (session_id) REFERENCES sessions(id) ON DELETE CASCADE,
                FOREIGN KEY (uploaded_by_user_id) REFERENCES users(id) ON DELETE SET NULL
            )
        """)
        
        # Create chat messages table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS chat_messages (
                id INT AUTO_INCREMENT PRIMARY KEY,
                session_id INT NOT NULL,
                user_id INT NOT NULL,
                pdf_id INT,
                message TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (session_id) REFERENCES sessions(id) ON DELETE CASCADE,
                FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
                FOREIGN KEY (pdf_id) REFERENCES pdfs(id) ON DELETE SET NULL
            )
        """)
        
        connection.commit()
        print("Database tables initialized successfully")
        
    except Error as e:
        print(f"Error initializing database: {e}")
        connection.rollback()
    finally:
        cursor.close()
        connection.close()
