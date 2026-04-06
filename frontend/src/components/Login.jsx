import { useState } from 'react'
import { authAPI } from '../utils/api'
import StudentRegister from './StudentRegister'
import './Login.css'

const Login = ({ onLoginSuccess }) => {
  const [showRegister, setShowRegister] = useState(false)
  const [credentials, setCredentials] = useState({ username: '', password: '' })
  const [error, setError] = useState('')
  const [loading, setLoading] = useState(false)

  const handleInputChange = (e) => {
    const { name, value } = e.target
    setCredentials(prev => ({ ...prev, [name]: value }))
    setError('')
  }

  const handleLogin = async (e) => {
    e.preventDefault()
    
    if (!credentials.username || !credentials.password) {
      setError('Username and password are required')
      return
    }

    setLoading(true)
    try {
      const response = await authAPI.login(credentials)
      localStorage.setItem('token', response.access_token)
      localStorage.setItem('user', JSON.stringify(response.user))
      onLoginSuccess(response.user)
    } catch (err) {
      setError(err.message || 'Login failed')
    } finally {
      setLoading(false)
    }
  }

  if (showRegister) {
    return <StudentRegister onSuccess={() => {
      setShowRegister(false)
      setCredentials({ username: '', password: '' })
    }} onBackToLogin={() => setShowRegister(false)} />
  }

  return (
    <div className="login-container">
      {/* ── Left decorative panel (desktop only) ── */}
      <div className="login-panel-left">
        <div className="login-panel-brand">
          <span className="login-panel-brand-icon">📚</span>
          <div>
            <div className="login-panel-brand-name">LibraryMS</div>
            <div className="login-panel-brand-sub">Management System</div>
          </div>
        </div>

        <div className="login-panel-tagline">
          <h2>Your reading journey starts here.</h2>
          <p>Borrow books, track due dates, manage reservations, and receive personalized recommendations — all in one place.</p>

          <ul className="login-feature-list">
            <li>
              <span className="login-feature-icon">📖</span>
              Browse thousands of books in real time
            </li>
            <li>
              <span className="login-feature-icon">🔔</span>
              Smart notifications for due dates &amp; availability
            </li>
            <li>
              <span className="login-feature-icon">🎯</span>
              Personalized recommendations by preference
            </li>
            <li>
              <span className="login-feature-icon">📋</span>
              Reservation queue with instant alerts
            </li>
          </ul>
        </div>

        <div style={{ opacity: 0.4, fontSize: '12px', color: '#fff' }}>
          © 2025 LibraryMS — Student &amp; Admin Portal
        </div>
      </div>

      {/* ── Right form panel ── */}
      <div className="login-panel-right">
        <div className="login-card">
          <div className="login-header">
            <div className="login-header-logo">
              <span className="login-header-logo-icon">📚</span>
              <span className="login-header-logo-name">LibraryMS</span>
            </div>
            <h1>Welcome back</h1>
            <p>Sign in to your student or admin account</p>
          </div>

          {error && <div className="error-message">{error}</div>}

          <form onSubmit={handleLogin}>
            <div className="form-group">
              <label>Username</label>
              <input
                type="text"
                name="username"
                value={credentials.username}
                onChange={handleInputChange}
                placeholder="Enter your username"
                disabled={loading}
              />
            </div>

            <div className="form-group">
              <label>Password</label>
              <input
                type="password"
                name="password"
                value={credentials.password}
                onChange={handleInputChange}
                placeholder="Enter your password"
                disabled={loading}
              />
            </div>

            <button type="submit" disabled={loading} className="btn btn-primary btn-login">
              {loading ? 'Signing in…' : '🔓 Sign In'}
            </button>
          </form>

          <div className="divider">OR</div>

          <button
            onClick={() => setShowRegister(true)}
            className="btn btn-secondary btn-register"
          >
            📝 Create Student Account
          </button>

          <div className="login-footer">
            <p><strong>Demo Credentials:</strong></p>
            <p><small>Admin: admin / admin123</small></p>
            <p><small>Student: rahul.kumar / pass123</small></p>
          </div>
        </div>
      </div>
    </div>
  )
}

export default Login
