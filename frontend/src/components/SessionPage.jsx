import React, { useState, useEffect, useRef } from 'react'
import { pdfAPI, chatAPI } from '../services/api'
import '../styles/SessionPage.css'

export function SessionPage({ sessionData, onLeaveSession }) {
  const [assignedPdf, setAssignedPdf] = useState(null)
  const [hasUploaded, setHasUploaded] = useState(false)
  const [uploadedFilename, setUploadedFilename] = useState('')
  const [messages, setMessages] = useState([])
  const [newMessage, setNewMessage] = useState('')
  const [loading, setLoading] = useState(false)
  const [allocating, setAllocating] = useState(false)
  const messagesEndRef = useRef(null)

  // Load upload status from localStorage on mount
  useEffect(() => {
    const savedUpload = localStorage.getItem(`uploaded_${sessionData.session_code}`)
    if (savedUpload) {
      setHasUploaded(true)
      setUploadedFilename(savedUpload)
    }
  }, [sessionData.session_code])

  useEffect(() => {
    loadAssignedPDF()
    
    // Poll for updates every 3 seconds
    const interval = setInterval(() => {
      loadAssignedPDF()
      if (assignedPdf) loadMessages()
    }, 3000)
    return () => clearInterval(interval)
  }, [sessionData])

  useEffect(() => {
    if (assignedPdf) {
      loadMessages()
    }
  }, [assignedPdf])

  useEffect(() => {
    scrollToBottom()
  }, [messages])

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' })
  }

  const loadAssignedPDF = async () => {
    try {
      const response = await pdfAPI.getMyAssignedPDF(
        sessionData.session_code,
        sessionData.user_token
      )
      if (response.data.assigned && response.data.pdf) {
        setAssignedPdf(response.data.pdf)
      }
    } catch (error) {
      console.error('Failed to load assigned PDF:', error)
    }
  }

  const loadMessages = async () => {
    if (!assignedPdf) return
    try {
      const response = await chatAPI.getSessionMessages(
        sessionData.session_code,
        sessionData.user_token
      )
      setMessages(response.data)
    } catch (error) {
      console.error('Failed to load messages:', error)
    }
  }

  const handleSendMessage = async (e) => {
    e.preventDefault()
    if (!newMessage.trim() || !assignedPdf) return

    setLoading(true)
    try {
      await chatAPI.sendMessage(
        sessionData.session_code,
        newMessage,
        assignedPdf.id,
        sessionData.user_token
      )
      setNewMessage('')
      await loadMessages()
    } catch (error) {
      alert('Failed to send message: ' + error.message)
    }
    setLoading(false)
  }

  const handleUploadPDF = async (e) => {
    const file = e.target.files[0]
    if (!file) return

    if (!file.name.toLowerCase().endsWith('.pdf')) {
      alert('Please upload a PDF file')
      return
    }

    setLoading(true)
    try {
      await pdfAPI.uploadPDF(
        sessionData.session_code,
        file,
        sessionData.user_token
      )
      setHasUploaded(true)
      setUploadedFilename(file.name)
      localStorage.setItem(`uploaded_${sessionData.session_code}`, file.name)
      alert('PDF uploaded successfully! Now request a random PDF from another user.')
      e.target.value = ''
    } catch (error) {
      const message = error.response?.data?.detail || error.message
      if (message.includes('only upload one PDF')) {
        setHasUploaded(true)
      }
      alert('Failed to upload PDF: ' + message)
    }
    setLoading(false)
  }

  const handleRequestAllocation = async () => {
    setAllocating(true)
    try {
      const response = await pdfAPI.requestAllocation(
        sessionData.session_code,
        sessionData.user_token
      )
      if (response.data.pdf) {
        setAssignedPdf(response.data.pdf)
        alert('PDF assigned! You received: ' + response.data.pdf.filename)
      } else {
        alert('No PDFs available yet. Wait for others to upload and try again.')
      }
    } catch (error) {
      const message = error.response?.data?.detail || error.message
      alert('Failed to request PDF: ' + message)
    }
    setAllocating(false)
  }

  const handleDownloadPDF = async () => {
    if (!assignedPdf) return
    try {
      const response = await pdfAPI.downloadPDF(
        assignedPdf.id,
        sessionData.user_token
      )
      const url = window.URL.createObjectURL(new Blob([response.data]))
      const link = document.createElement('a')
      link.href = url
      link.setAttribute('download', assignedPdf.filename)
      document.body.appendChild(link)
      link.click()
      link.parentElement.removeChild(link)
    } catch (error) {
      alert('Failed to download PDF: ' + error.message)
    }
  }

  return (
    <div className="session-container">
      <div className="session-header">
        <div className="header-info">
          <h2>Session: {sessionData.session_code}</h2>
          <p className="session-tip">Share this code with others to join!</p>
        </div>
        <button className="button-leave" onClick={onLeaveSession}>
          Leave Session
        </button>
      </div>

      <div className="session-content">
        <div className="pdfs-panel">
          {/* Upload Section */}
          <div className="panel-section">
            <div className="panel-header">
              <h3>Your Upload</h3>
            </div>
            {hasUploaded ? (
              <div className="upload-status success">
                <p>Uploaded: <strong>{uploadedFilename || 'Your PDF'}</strong></p>
                <p className="upload-note">You can only upload one PDF per session</p>
              </div>
            ) : (
              <div className="upload-area">
                <p className="upload-hint">Upload ONE PDF to share anonymously</p>
                <label className="upload-label">
                  <input
                    type="file"
                    accept=".pdf"
                    onChange={handleUploadPDF}
                    disabled={loading}
                    className="upload-input"
                  />
                  <span className="upload-button">
                    {loading ? 'Uploading...' : '+ Upload PDF'}
                  </span>
                </label>
              </div>
            )}
          </div>

          {/* Assigned PDF Section */}
          <div className="panel-section">
            <div className="panel-header">
              <h3>Your Assigned PDF</h3>
            </div>
            {assignedPdf ? (
              <div className="assigned-pdf-card">
                <div className="pdf-info">
                  <p className="pdf-name">{assignedPdf.filename}</p>
                  <p className="pdf-note">This is a random PDF from another user</p>
                </div>
                <button 
                  className="download-btn-large" 
                  onClick={handleDownloadPDF}
                >
                  Download PDF
                </button>
              </div>
            ) : (
              <div className="no-assigned-pdf">
                <p>No PDF assigned yet</p>
                <button
                  className="request-btn"
                  onClick={handleRequestAllocation}
                  disabled={allocating}
                >
                  {allocating ? 'Finding...' : 'Get Random PDF'}
                </button>
                <p className="hint">You will receive a random PDF uploaded by another user</p>
              </div>
            )}
          </div>
        </div>

        <div className="chat-panel">
          <div className="panel-header">
            <h3>Discussion</h3>
            {assignedPdf && <span className="pdf-badge">{assignedPdf.filename}</span>}
          </div>

          <div className="messages-container">
            {!assignedPdf ? (
              <p className="empty-message">Get a PDF assigned to start chatting!</p>
            ) : messages.length === 0 ? (
              <p className="empty-message">No messages yet. Start discussing!</p>
            ) : (
              messages.map((msg) => (
                <div key={msg.id} className="message">
                  <div className="message-header">
                    <span className="message-user">Anonymous User</span>
                    <span className="message-time">
                      {new Date(msg.created_at).toLocaleTimeString()}
                    </span>
                  </div>
                  <p className="message-text">{msg.message}</p>
                </div>
              ))
            )}
            <div ref={messagesEndRef} />
          </div>

          <form className="message-form" onSubmit={handleSendMessage}>
            <input
              type="text"
              value={newMessage}
              onChange={(e) => setNewMessage(e.target.value)}
              placeholder={assignedPdf ? "Discuss the PDF anonymously..." : "Get a PDF first to chat..."}
              disabled={!assignedPdf || loading}
              className="message-input"
            />
            <button
              type="submit"
              disabled={!assignedPdf || !newMessage.trim() || loading}
              className="send-button"
            >
              Send
            </button>
          </form>
        </div>
      </div>
    </div>
  )
}
