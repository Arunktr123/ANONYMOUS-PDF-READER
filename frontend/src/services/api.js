import axios from 'axios'

// Use Render backend URL in production, local proxy in development
const API_BASE = import.meta.env.PROD 
  ? 'https://anonymous-pdf-reader.onrender.com/api' 
  : '/api'

export const api = axios.create({
  baseURL: API_BASE,
})

// Session API
export const sessionAPI = {
  createSession: () => api.post('/sessions/create'),
  joinSession: (sessionCode) => api.post('/sessions/join', { session_code: sessionCode }),
  getSessionInfo: (sessionCode) => api.get(`/sessions/${sessionCode}`),
}

// PDF API
export const pdfAPI = {
  uploadPDF: (sessionCode, file, userToken) => {
    const formData = new FormData()
    formData.append('file', file)
    return api.post(`/pdfs/upload/${sessionCode}`, formData, {
      headers: {
        'X-User-Token': userToken,
        'Content-Type': 'multipart/form-data',
      },
    })
  },
  getSessionPDFs: (sessionCode, userToken) =>
    api.get(`/pdfs/session/${sessionCode}`, {
      headers: { 'X-User-Token': userToken },
    }),
  downloadPDF: (pdfId, userToken) =>
    api.get(`/pdfs/download/${pdfId}`, {
      headers: { 'X-User-Token': userToken },
      responseType: 'blob',
    }),
  requestAllocation: (sessionCode, userToken) =>
    api.post(`/pdfs/request-allocation/${sessionCode}`, {}, {
      headers: { 'X-User-Token': userToken },
    }),
  getMyAssignedPDF: (sessionCode, userToken) =>
    api.get(`/pdfs/my-assigned/${sessionCode}`, {
      headers: { 'X-User-Token': userToken },
    }),
}

// Chat API
export const chatAPI = {
  sendMessage: (sessionCode, message, pdfId, userToken) =>
    api.post(`/chat/${sessionCode}/send`, { message, pdf_id: pdfId }, {
      headers: { 'X-User-Token': userToken },
    }),
  getSessionMessages: (sessionCode, userToken, limit = 100) =>
    api.get(`/chat/${sessionCode}/messages?limit=${limit}`, {
      headers: { 'X-User-Token': userToken },
    }),
  getPDFMessages: (sessionCode, pdfId, userToken) =>
    api.get(`/chat/${sessionCode}/pdf/${pdfId}/messages`, {
      headers: { 'X-User-Token': userToken },
    }),
}
