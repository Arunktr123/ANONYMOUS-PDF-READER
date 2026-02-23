# Anonymous PDF Reader Chat

A session-based anonymous PDF sharing and discussion application.

## Quick Start

### 1. Setup MySQL Database
```sql
CREATE DATABASE pdf_chat_db;
```

### 2. Backend Setup
```bash
cd backend
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
python main.py
```
Backend runs on http://localhost:8000

### 3. Frontend Setup
```bash
cd frontend
npm install
npm run dev
```
Frontend runs on http://localhost:3000

## Features
- Session-based PDF rooms
- Anonymous user participation
- Random PDF allocation
- Real-time chat
- PDF upload/download

## API Docs
http://localhost:8000/docs
