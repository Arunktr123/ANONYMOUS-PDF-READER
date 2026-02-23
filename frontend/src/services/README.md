# API Service Documentation

This file handles all HTTP communication between the **React frontend** and **FastAPI backend**.

---

## Architecture Overview

```
┌─────────────────────────────────────────────────────────────────┐
│                      FRONTEND (React)                          │
│                                                                 │
│   ┌─────────────┐    ┌─────────────┐    ┌─────────────┐       │
│   │  HomePage   │    │ SessionPage │    │  Components │       │
│   └──────┬──────┘    └──────┬──────┘    └──────┬──────┘       │
│          │                  │                  │               │
│          └──────────────────┼──────────────────┘               │
│                             │                                   │
│                             ▼                                   │
│                    ┌─────────────────┐                         │
│                    │    api.js       │  ◀── THIS FILE          │
│                    │  (Axios Client) │                         │
│                    └────────┬────────┘                         │
│                             │                                   │
└─────────────────────────────┼───────────────────────────────────┘
                              │ HTTP Requests
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                     VITE PROXY                                  │
│            /api/* → http://localhost:8000/api/*                │
└─────────────────────────────┼───────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                      BACKEND (FastAPI)                         │
│                    http://localhost:8000                       │
└─────────────────────────────────────────────────────────────────┘
```

---

## API Modules Breakdown

### 1️⃣ Base Configuration

```javascript
const API_BASE = '/api'  // Uses Vite proxy - works on any device

export const api = axios.create({
  baseURL: API_BASE,
})
```

| Setting | Purpose |
|---------|---------|
| `/api` | Relative URL, proxied by Vite to backend |
| `axios.create()` | Creates reusable HTTP client instance |

---

### 2️⃣ Session API

Handles session creation and joining.

```javascript
export const sessionAPI = {
  createSession: () => api.post('/sessions/create'),
  joinSession: (sessionCode) => api.post('/sessions/join', { session_code: sessionCode }),
  getSessionInfo: (sessionCode) => api.get(`/sessions/${sessionCode}`),
}
```

| Method | Endpoint | Purpose |
|--------|----------|---------|
| `createSession()` | `POST /api/sessions/create` | Generate new session code |
| `joinSession(code)` | `POST /api/sessions/join` | Join session & get JWT token |
| `getSessionInfo(code)` | `GET /api/sessions/{code}` | Get session details |

**Flow:**
```
createSession() ──▶ Returns session_code: "ABC12345"
       │
       ▼
joinSession("ABC12345") ──▶ Returns user_token (JWT)
```

---

### 3️⃣ PDF API

Handles all PDF operations.

```javascript
export const pdfAPI = {
  uploadPDF: (sessionCode, file, userToken) => {...},
  getSessionPDFs: (sessionCode, userToken) => {...},
  downloadPDF: (pdfId, userToken) => {...},
  requestAllocation: (sessionCode, userToken) => {...},
  getMyAssignedPDF: (sessionCode, userToken) => {...},
}
```

| Method | Endpoint | Headers | Purpose |
|--------|----------|---------|---------|
| `uploadPDF()` | `POST /api/pdfs/upload/{code}` | `X-User-Token`, `Content-Type: multipart/form-data` | Upload PDF (1 per user) |
| `getSessionPDFs()` | `GET /api/pdfs/session/{code}` | `X-User-Token` | List all PDFs in session |
| `downloadPDF()` | `GET /api/pdfs/download/{id}` | `X-User-Token` | Download PDF as blob |
| `requestAllocation()` | `POST /api/pdfs/request-allocation/{code}` | `X-User-Token` | Get random PDF (not your own) |
| `getMyAssignedPDF()` | `GET /api/pdfs/my-assigned/{code}` | `X-User-Token` | Check your assigned PDF |

**Upload Flow:**
```
┌──────────────┐     ┌──────────────────┐     ┌──────────────┐
│ Select File  │────▶│ FormData + Token │────▶│  Backend     │
│ (PDF only)   │     │ X-User-Token     │     │  Saves file  │
└──────────────┘     └──────────────────┘     └──────────────┘
```

**Allocation Flow:**
```
requestAllocation()
        │
        ▼
┌─────────────────────────────────────┐
│ Backend finds random PDF where:    │
│ - Same session                     │
│ - NOT uploaded by requesting user  │
│ - Not already assigned to user     │
└─────────────────────────────────────┘
        │
        ▼
Returns: { pdf: { id: 2, filename: "other_user.pdf" } }
```

---

### 4️⃣ Chat API

Handles anonymous messaging.

```javascript
export const chatAPI = {
  sendMessage: (sessionCode, message, pdfId, userToken) => {...},
  getSessionMessages: (sessionCode, userToken, limit = 100) => {...},
  getPDFMessages: (sessionCode, pdfId, userToken) => {...},
}
```

| Method | Endpoint | Purpose |
|--------|----------|---------|
| `sendMessage()` | `POST /api/chat/{code}/send` | Send anonymous message |
| `getSessionMessages()` | `GET /api/chat/{code}/messages` | Get all session messages |
| `getPDFMessages()` | `GET /api/chat/{code}/pdf/{id}/messages` | Get messages for specific PDF |

**Chat Flow:**
```
┌─────────────┐                              ┌─────────────┐
│   User A    │ ──── sendMessage() ────────▶ │   Backend   │
│             │                              │   MySQL DB  │
│             │ ◀─── getSessionMessages() ── │             │
└─────────────┘      (polled every 3s)       └─────────────┘
                                                   │
┌─────────────┐                                    │
│   User B    │ ◀─── getSessionMessages() ─────────┘
│             │      (polled every 3s)
└─────────────┘
```

---

## HTTP Headers Reference

| Header | Value | Used In |
|--------|-------|---------|
| `X-User-Token` | JWT token from join | All authenticated requests |
| `Content-Type` | `application/json` | Most requests (auto) |
| `Content-Type` | `multipart/form-data` | PDF upload |

---

## Request/Response Examples

### Create Session
```http
POST /api/sessions/create

Response 200:
{
  "id": 1,
  "session_code": "ABC12345",
  "created_at": "2026-02-23T10:00:00"
}
```

### Join Session
```http
POST /api/sessions/join
Content-Type: application/json

Body: { "session_code": "ABC12345" }

Response 200:
{
  "user_token": "eyJhbGciOiJIUzI1NiJ9.eyJzZXNzaW9uX2NvZGUiOiJBQkMxMjM0NSJ9...",
  "user_id": 1,
  "session_id": 1
}
```

### Upload PDF
```http
POST /api/pdfs/upload/ABC12345
Content-Type: multipart/form-data
X-User-Token: eyJhbGciOiJIUzI1NiJ9...

Body: [PDF file binary]

Response 200: { "message": "PDF uploaded successfully", "filename": "doc.pdf" }
Response 400: { "detail": "You can only upload one PDF per session" }
```

### Get Random PDF
```http
POST /api/pdfs/request-allocation/ABC12345
X-User-Token: eyJhbGciOiJIUzI1NiJ9...

Response 200:
{
  "message": "PDF assigned successfully",
  "pdf": { "id": 2, "filename": "anonymous_doc.pdf" }
}
```

### Send Chat Message
```http
POST /api/chat/ABC12345/send
Content-Type: application/json
X-User-Token: eyJhbGciOiJIUzI1NiJ9...

Body: { "message": "What do you think about page 3?", "pdf_id": 2 }

Response 200:
{
  "id": 1,
  "session_id": 1,
  "user_id": 1,
  "pdf_id": 2,
  "message": "What do you think about page 3?",
  "created_at": "2026-02-23T10:05:00"
}
```

### Get Messages
```http
GET /api/chat/ABC12345/messages?limit=100
X-User-Token: eyJhbGciOiJIUzI1NiJ9...

Response 200:
[
  {
    "id": 1,
    "user_id": 1,
    "pdf_id": 2,
    "message": "What do you think about page 3?",
    "created_at": "2026-02-23T10:05:00"
  },
  {
    "id": 2,
    "user_id": 2,
    "pdf_id": 3,
    "message": "I found something interesting!",
    "created_at": "2026-02-23T10:06:00"
  }
]
```

---

## Security Features

| Feature | Implementation |
|---------|----------------|
| **Authentication** | JWT token in `X-User-Token` header |
| **Session Binding** | Token contains `session_code` - validated on each request |
| **One PDF Rule** | Backend checks upload count per user per session |
| **Anonymous Allocation** | Excludes user's own PDFs from random selection |
| **Token Expiry** | JWT tokens expire after 24 hours |

---

## Error Handling

| Status Code | Meaning | Example |
|-------------|---------|---------|
| `200` | Success | Request completed |
| `400` | Bad Request | "You can only upload one PDF per session" |
| `401` | Unauthorized | "Invalid user token" or "Token does not belong to this session" |
| `404` | Not Found | "Session not found" or "PDF not found" |
| `422` | Validation Error | Missing required fields |
| `500` | Server Error | Database or file system errors |

---

## File Structure

```
frontend/src/services/
├── api.js          # Main API service (this file's source)
└── README.md       # This documentation
```

---

## Usage Examples in Components

### HomePage.jsx
```javascript
import { sessionAPI } from '../services/api'

// Create new session
const response = await sessionAPI.createSession()
const sessionCode = response.data.session_code

// Join session
const joinResponse = await sessionAPI.joinSession(sessionCode)
const userToken = joinResponse.data.user_token
```

### SessionPage.jsx
```javascript
import { pdfAPI, chatAPI } from '../services/api'

// Upload PDF
await pdfAPI.uploadPDF(sessionCode, file, userToken)

// Request random PDF
const allocation = await pdfAPI.requestAllocation(sessionCode, userToken)

// Send message
await chatAPI.sendMessage(sessionCode, message, pdfId, userToken)

// Get messages (polled every 3 seconds)
const messages = await chatAPI.getSessionMessages(sessionCode, userToken)
```

---

## Configuration

The API uses Vite's proxy configuration for development:

```javascript
// vite.config.js
export default {
  server: {
    proxy: {
      '/api': {
        target: 'http://localhost:8000',
        changeOrigin: true,
      }
    }
  }
}
```

This allows the frontend to make requests to `/api/*` which are automatically proxied to the backend server, avoiding CORS issues during development.
