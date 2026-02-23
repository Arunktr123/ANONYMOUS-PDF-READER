import React, { useState } from 'react'
import { sessionAPI } from '../services/api'
import '../styles/HomePage.css'

export function HomePage({ onSessionCreated }) {
  const [sessionCode, setSessionCode] = useState('')
  const [loading, setLoading] = useState(false)

  const handleCreateSession = async () => {
    setLoading(true)
    try {
      const response = await sessionAPI.createSession()
      const sessionCode = response.data.session_code
      // Creator also joins to get a user_token
      const joinResponse = await sessionAPI.joinSession(sessionCode)
      onSessionCreated({
        ...response.data,
        ...joinResponse.data,
      })
    } catch (error) {
      alert('Failed to create session: ' + error.message)
    }
    setLoading(false)
  }

  const handleJoinSession = async () => {
    if (!sessionCode.trim()) {
      alert('Please enter a session code')
      return
    }
    setLoading(true)
    try {
      const joinResponse = await sessionAPI.joinSession(sessionCode)
      const sessionResponse = await sessionAPI.getSessionInfo(sessionCode)
      onSessionCreated({
        ...sessionResponse.data.session,
        session_code: sessionCode,
        ...joinResponse.data,  // user_token comes last to not be overwritten
      })
    } catch (error) {
      alert('Failed to join session: ' + error.message)
    }
    setLoading(false)
  }

  return (
    <div className="home-container">
      <div className="home-card">
        <div className="brand-header">
          <img src="/logo.png" alt="Supernatural Logo" className="brand-logo" />
          <span className="brand-name">SUPERNATURAL</span>
        </div>
        <h1>📄 Anonymous PDF Chat</h1>
        <p className="subtitle">Share and discuss PDFs anonymously</p>
        
        <div className="action-section">
          <button 
            className="button button-primary"
            onClick={handleCreateSession}
            disabled={loading}
          >
            {loading ? 'Creating...' : '+ Create New Session'}
          </button>
        </div>

        <div className="divider">OR</div>

        <div className="join-section">
          <input
            type="text"
            placeholder="Enter session code"
            value={sessionCode}
            onChange={(e) => setSessionCode(e.target.value.toUpperCase())}
            className="session-input"
            onKeyPress={(e) => e.key === 'Enter' && handleJoinSession()}
          />
          <button 
            className="button button-secondary"
            onClick={handleJoinSession}
            disabled={loading}
          >
            {loading ? 'Joining...' : 'Join Session'}
          </button>
        </div>

        <div className="info-box">
          <h3>How it works:</h3>
          <ul>
            <li>Create a session and share the code with others</li>
            <li>Upload PDFs to share with the session</li>
            <li>Get randomly assigned a PDF to discuss</li>
            <li>Chat anonymously about PDFs with other users</li>
          </ul>
        </div>
      </div>
    </div>
  )
}
