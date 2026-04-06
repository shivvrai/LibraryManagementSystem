import { useState, useEffect } from 'react'
import { getToken, logout } from './utils/auth'
import { ToastProvider } from './components/ui/Toast'
import Login from './components/Login'
import AdminDashboard from './components/admin/AdminDashboard'
import StudentDashboard from './components/student/StudentDashboard'
import './App.css'

function App() {
  const [user, setUser] = useState(null)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    // Apply saved theme on mount
    const savedTheme = localStorage.getItem('theme')
    if (savedTheme) {
      document.documentElement.setAttribute('data-color-scheme', savedTheme)
    } else {
      const prefersDark = window.matchMedia('(prefers-color-scheme: dark)').matches
      document.documentElement.setAttribute('data-color-scheme', prefersDark ? 'dark' : 'light')
    }

    const token = getToken()
    const storedUser = localStorage.getItem('user')
    
    if (token && storedUser) {
      try {
        setUser(JSON.parse(storedUser))
      } catch (err) {
        logout()
      }
    }
    
    setLoading(false)
  }, [])

  const handleLoginSuccess = (userData) => {
    setUser(userData)
  }

  const handleLogout = () => {
    logout()
    setUser(null)
  }

  if (loading) {
    return (
      <div className="loading-container">
        <div className="spinner" />
        <p>Loading Library...</p>
      </div>
    )
  }

  if (!user) {
    return (
      <ToastProvider>
        <Login onLoginSuccess={handleLoginSuccess} />
      </ToastProvider>
    )
  }

  return (
    <ToastProvider>
      {user.role === 'admin' && (
        <AdminDashboard user={user} onLogout={handleLogout} />
      )}
      {user.role === 'student' && (
        <StudentDashboard user={user} onLogout={handleLogout} />
      )}
    </ToastProvider>
  )
}

export default App
