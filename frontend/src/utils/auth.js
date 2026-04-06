// Authentication utilities

const API_BASE = import.meta.env.VITE_API_URL || 'http://localhost:5000/api'

export const login = async (username, password) => {
  try {
    const response = await fetch(`${API_BASE}/auth/login`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json'
      },
      body: JSON.stringify({ username, password })
    })

    if (response.ok) {
      const data = await response.json()
      localStorage.setItem('token', data.token)
      localStorage.setItem('user', JSON.stringify(data.user))
      return true
    }
    return false
  } catch (error) {
    console.error('Login error:', error)
    return false
  }
}

export const logout = () => {
  localStorage.removeItem('token')
  localStorage.removeItem('user')
}

export const getToken = () => {
  return localStorage.getItem('token')
}

export const getUser = () => {
  const userStr = localStorage.getItem('user')
  if (userStr) {
    try {
      return JSON.parse(userStr)
    } catch (error) {
      console.error('Failed to parse user:', error)
      return null
    }
  }
  return null
}

export const isAuthenticated = () => {
  return !!getToken()
}
