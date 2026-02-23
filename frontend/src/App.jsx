import React, { useState, useEffect } from 'react'
import { HomePage } from './components/HomePage'
import { SessionPage } from './components/SessionPage'
import { Analytics } from "@vercel/analytics/next"
import './App.css'

export default function App() {
  const [sessionData, setSessionData] = useState(null)
  const [loading, setLoading] = useState(true)

  // Load session from localStorage on app start
  useEffect(() => {
    const savedSession = localStorage.getItem('current_session')
    if (savedSession) {
      try {
        const data = JSON.parse(savedSession)
        if (data && data.session_code && data.user_token) {
          setSessionData(data)
        }
      } catch (error) {
        console.error('Failed to load saved session:', error)
        localStorage.removeItem('current_session')
      }
    }
    setLoading(false)
  }, [])

  const handleSessionCreated = (data) => {
    setSessionData(data)
    localStorage.setItem('current_session', JSON.stringify(data))
  }

  const handleLeaveSession = () => {
    if (sessionData) {
      localStorage.removeItem('current_session')
      localStorage.removeItem(`uploaded_${sessionData.session_code}`)
    }
    setSessionData(null)
  }

  if (loading) {
    return (
      <div className="app loading-screen">
        <div className="spinner"></div>
        <p>Loading...</p>
      </div>
    )
  }

  return (
    <div className="app">
      {!sessionData ? (
        <HomePage onSessionCreated={handleSessionCreated} />
      ) : (
        <SessionPage sessionData={sessionData} onLeaveSession={handleLeaveSession} />
      )}
    </div>
  )
}
