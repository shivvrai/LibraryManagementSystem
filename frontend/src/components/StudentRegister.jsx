import { useState, useEffect } from 'react'
import { authAPI } from '../utils/api'
import './StudentRegister.css'

const StudentRegister = ({ onSuccess, onBackToLogin }) => {
  const [formData, setFormData] = useState({
    name: '',
    email: '',
    phone: '',
    username: '',
    password: '',
    confirmPassword: ''
  })
  
  const [errors, setErrors] = useState({})
  const [loading, setLoading] = useState(false)
  const [usernameStatus, setUsernameStatus] = useState(null) // 'available', 'taken', null
  const [suggestions, setSuggestions] = useState([])
  const [registrationNo, setRegistrationNo] = useState(null)

  // Check username availability with debounce
  useEffect(() => {
    if (!formData.username || formData.username.length < 3) {
      setUsernameStatus(null)
      return
    }

    const timer = setTimeout(async () => {
      try {
        const response = await authAPI.checkUsername(formData.username)
        setUsernameStatus(response.available ? 'available' : 'taken')
      } catch (err) {
        setUsernameStatus(null)
      }
    }, 500)

    return () => clearTimeout(timer)
  }, [formData.username])

  // Get username suggestions when name changes
  useEffect(() => {
    if (!formData.name || formData.name.length < 2) {
      setSuggestions([])
      return
    }

    const timer = setTimeout(async () => {
      try {
        const response = await authAPI.suggestUsernames(formData.name)
        setSuggestions(response.suggestions || [])
      } catch (err) {
        setSuggestions([])
      }
    }, 500)

    return () => clearTimeout(timer)
  }, [formData.name])

  const validateForm = () => {
    const newErrors = {}

    if (!formData.name.trim()) {
      newErrors.name = 'Full name is required'
    }

    if (!formData.email.trim()) {
      newErrors.email = 'Email is required'
    } else if (!/\S+@\S+\.\S+/.test(formData.email)) {
      newErrors.email = 'Invalid email format'
    }

    if (!formData.phone.trim()) {
      newErrors.phone = 'Phone number is required'
    } else if (!/^\d{10}$/.test(formData.phone.replace(/\D/g, ''))) {
      newErrors.phone = 'Phone must be 10 digits'
    }

    if (!formData.username.trim()) {
      newErrors.username = 'Username is required'
    } else if (formData.username.length < 3) {
      newErrors.username = 'Username must be at least 3 characters'
    } else if (usernameStatus === 'taken') {
      newErrors.username = 'Username is already taken'
    }

    if (!formData.password) {
      newErrors.password = 'Password is required'
    } else if (formData.password.length < 6) {
      newErrors.password = 'Password must be at least 6 characters'
    }

    if (formData.password !== formData.confirmPassword) {
      newErrors.confirmPassword = 'Passwords do not match'
    }

    setErrors(newErrors)
    return Object.keys(newErrors).length === 0
  }

  const handleInputChange = (e) => {
    const { name, value } = e.target
    setFormData(prev => ({
      ...prev,
      [name]: value
    }))
  }

  const useSuggestion = (suggestion) => {
    setFormData(prev => ({
      ...prev,
      username: suggestion
    }))
    setSuggestions([])
  }

  const handleSubmit = async (e) => {
    e.preventDefault()

    if (!validateForm()) return

    setLoading(true)
    try {
      const response = await authAPI.register({
        name: formData.name,
        email: formData.email,
        phone: formData.phone,
        username: formData.username,
        password: formData.password
      })

      setRegistrationNo(response.registration_no)
      
      // Show success message for 2 seconds, then redirect to login
      setTimeout(() => {
        onSuccess()
      }, 2000)
    } catch (err) {
      setErrors({ submit: err.message })
    } finally {
      setLoading(false)
    }
  }

  if (registrationNo) {
    return (
      <div className="register-container">
        <div className="success-message">
          <h2>✅ Registration Successful!</h2>
          <p>Your account has been created successfully.</p>
          <p>Your Registration Number: <strong>{registrationNo}</strong></p>
          <p>You can now login with your username and password.</p>
          <p style={{fontSize: '0.9em', color: '#666', marginTop: '10px'}}>
            Redirecting to login page...
          </p>
        </div>
      </div>
    )
  }

  return (
    <div className="register-container">
      <div className="register-card">
        <h1>📚 Student Registration</h1>
        <p className="subtitle">Create your library account</p>

        {errors.submit && <div className="error-message">{errors.submit}</div>}

        <form onSubmit={handleSubmit}>
          <div className="form-group">
            <label>Full Name *</label>
            <input
              type="text"
              name="name"
              value={formData.name}
              onChange={handleInputChange}
              placeholder="Enter your full name"
              className={errors.name ? 'error' : ''}
            />
            {errors.name && <span className="error-text">{errors.name}</span>}
          </div>

          <div className="form-row">
            <div className="form-group">
              <label>Email *</label>
              <input
                type="email"
                name="email"
                value={formData.email}
                onChange={handleInputChange}
                placeholder="your@email.com"
                className={errors.email ? 'error' : ''}
              />
              {errors.email && <span className="error-text">{errors.email}</span>}
            </div>

            <div className="form-group">
              <label>Phone *</label>
              <input
                type="tel"
                name="phone"
                value={formData.phone}
                onChange={handleInputChange}
                placeholder="10-digit phone number"
                className={errors.phone ? 'error' : ''}
              />
              {errors.phone && <span className="error-text">{errors.phone}</span>}
            </div>
          </div>

          <div className="form-group">
            <label>Username *</label>
            <div className="username-input-wrapper">
              <input
                type="text"
                name="username"
                value={formData.username}
                onChange={handleInputChange}
                placeholder="Choose a username"
                className={errors.username ? 'error' : usernameStatus === 'available' ? 'success' : usernameStatus === 'taken' ? 'error' : ''}
              />
              {usernameStatus === 'available' && <span className="status-icon">✓</span>}
              {usernameStatus === 'taken' && <span className="status-icon">✗</span>}
            </div>
            {errors.username && <span className="error-text">{errors.username}</span>}

            {suggestions.length > 0 && (
              <div className="suggestions">
                <p className="suggestions-label">💡 Suggested usernames:</p>
                <div className="suggestions-list">
                  {suggestions.map((suggestion, idx) => (
                    <button
                      key={idx}
                      type="button"
                      className="suggestion-btn"
                      onClick={() => useSuggestion(suggestion)}
                    >
                      {suggestion}
                    </button>
                  ))}
                </div>
              </div>
            )}
          </div>

          <div className="form-row">
            <div className="form-group">
              <label>Password *</label>
              <input
                type="password"
                name="password"
                value={formData.password}
                onChange={handleInputChange}
                placeholder="Min. 6 characters"
                className={errors.password ? 'error' : ''}
              />
              {errors.password && <span className="error-text">{errors.password}</span>}
            </div>

            <div className="form-group">
              <label>Confirm Password *</label>
              <input
                type="password"
                name="confirmPassword"
                value={formData.confirmPassword}
                onChange={handleInputChange}
                placeholder="Re-enter password"
                className={errors.confirmPassword ? 'error' : ''}
              />
              {errors.confirmPassword && <span className="error-text">{errors.confirmPassword}</span>}
            </div>
          </div>

          <button type="submit" disabled={loading} className="btn btn-primary btn-submit">
            {loading ? 'Creating Account...' : '✓ Create Account'}
          </button>
        </form>

        <div className="login-link">
          Already have an account? <button onClick={onBackToLogin} className="link-btn">Login here</button>
        </div>
      </div>
    </div>
  )
}

export default StudentRegister
