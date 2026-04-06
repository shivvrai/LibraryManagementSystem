import { useState, useEffect } from 'react'
import BookManager from './BookManager'
import { logout } from '../utils/auth'

const Dashboard = ({ onLogout }) => {
  const [books, setBooks] = useState([])
  const [stats, setStats] = useState({})
  const [searchTerm, setSearchTerm] = useState('')
  const [categoryFilter, setCategoryFilter] = useState('')
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')
  const [successMessage, setSuccessMessage] = useState('')

  useEffect(() => {
    fetchBooks()
  }, [])

  useEffect(() => {
    if (books.length >= 0) {
      fetchStats()
    }
  }, [books])

  const fetchBooks = async () => {
    try {
      setLoading(true)
      const token = localStorage.getItem('token')
      const response = await fetch('http://localhost:5000/api/books', {
        headers: {
          'Authorization': `Bearer ${token}`
        }
      })

      if (response.ok) {
        const data = await response.json()
        setBooks(data)
        setError('')
      } else if (response.status === 401) {
        handleLogout()
      } else {
        throw new Error('Failed to fetch books')
      }
    } catch (err) {
      setError('Failed to load books')
      console.error('Fetch books error:', err)
    } finally {
      setLoading(false)
    }
  }

  const fetchStats = async () => {
    try {
      const token = localStorage.getItem('token')
      const response = await fetch('http://localhost:5000/api/books/stats', {
        headers: {
          'Authorization': `Bearer ${token}`
        }
      })

      if (response.ok) {
        const data = await response.json()
        setStats(data)
      }
    } catch (err) {
      console.error('Failed to fetch stats:', err)
    }
  }

  const handleLogout = () => {
    logout()
    onLogout()
  }

  const handleDeleteBook = async (id) => {
    if (!window.confirm('Are you sure you want to delete this book?')) return

    try {
      const token = localStorage.getItem('token')
      const response = await fetch(`http://localhost:5000/api/books/${id}`, {
        method: 'DELETE',
        headers: {
          'Authorization': `Bearer ${token}`
        }
      })

      if (response.ok) {
        setBooks(books.filter(book => book.id !== id))
        setSuccessMessage('Book deleted successfully')
        setTimeout(() => setSuccessMessage(''), 3000)
        fetchStats()
      } else {
        throw new Error('Failed to delete book')
      }
    } catch (err) {
      setError('Failed to delete book')
      console.error('Delete error:', err)
    }
  }

  // NEW: Update quantity function
  const updateQuantity = async (bookId, newQuantity) => {
    if (newQuantity < 0) return // Prevent negative quantities

    try {
      const token = localStorage.getItem('token')
      const response = await fetch(`http://localhost:5000/api/books/${bookId}`, {
        method: 'PUT',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${token}`
        },
        body: JSON.stringify({ quantity: newQuantity })
      })

      if (response.ok) {
        const updatedBook = await response.json()
        setBooks(books.map(book => 
          book.id === bookId ? { ...book, quantity: newQuantity } : book
        ))
        setSuccessMessage('Quantity updated successfully')
        setTimeout(() => setSuccessMessage(''), 3000)
        fetchStats()
      } else {
        throw new Error('Failed to update quantity')
      }
    } catch (err) {
      setError('Failed to update quantity')
      console.error('Update quantity error:', err)
    }
  }

  const handleBookAdded = () => {
    fetchBooks()
    setSuccessMessage('Book added successfully')
    setTimeout(() => setSuccessMessage(''), 3000)
  }

  const filteredBooks = books.filter(book => {
    const matchesSearch = !searchTerm || 
      book.title.toLowerCase().includes(searchTerm.toLowerCase()) ||
      book.author.toLowerCase().includes(searchTerm.toLowerCase()) ||
      book.isbn.includes(searchTerm)

    const matchesCategory = !categoryFilter || 
      book.category.toLowerCase() === categoryFilter.toLowerCase()

    return matchesSearch && matchesCategory
  })

  const categories = [...new Set(books.map(b => b.category))]

  if (loading && books.length === 0) {
    return <div className="loading-container">Loading...</div>
  }

  return (
    <div className="dashboard">
      <header className="dashboard-header">
        <div className="header-content">
          <h1>📚 Library Management System</h1>
          <button onClick={handleLogout} className="logout-btn">
            Logout
          </button>
        </div>
      </header>

      {error && (
        <div className="alert alert-error">
          <span>❌ {error}</span>
          <button onClick={() => setError('')}>×</button>
        </div>
      )}

      {successMessage && (
        <div className="alert alert-success">
          <span>✅ {successMessage}</span>
          <button onClick={() => setSuccessMessage('')}>×</button>
        </div>
      )}

      <div className="stats-container">
        <div className="stat-card">
          <div className="stat-icon">📖</div>
          <h3>Total Books</h3>
          <p className="stat-number">{stats.total_books || 0}</p>
        </div>

        <div className="stat-card">
          <div className="stat-icon">📦</div>
          <h3>Total Quantity</h3>
          <p className="stat-number">{stats.total_quantity || 0}</p>
        </div>

        <div className="stat-card">
          <div className="stat-icon">💰</div>
          <h3>Total Value</h3>
          <p className="stat-number">${stats.total_value || 0}</p>
        </div>

        <div className="stat-card">
          <div className="stat-icon">📊</div>
          <h3>Categories</h3>
          <p className="stat-number">{stats.categories || 0}</p>
        </div>

        <div className="stat-card">
          <div className="stat-icon">📄</div>
          <h3>Avg Pages</h3>
          <p className="stat-number">{stats.avg_pages || 0}</p>
        </div>

        <div className="stat-card">
          <div className="stat-icon">💵</div>
          <h3>Avg Price</h3>
          <p className="stat-number">${stats.avg_price || 0}</p>
        </div>
      </div>

      <BookManager onBookAdded={handleBookAdded} />

      <div className="filters-section">
        <div className="search-container">
          <input
            type="text"
            placeholder="🔍 Search by title, author, or ISBN..."
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
            className="search-input"
          />
        </div>

        <div className="category-filter">
          <select
            value={categoryFilter}
            onChange={(e) => setCategoryFilter(e.target.value)}
            className="category-select"
          >
            <option value="">All Categories</option>
            {categories.map(cat => (
              <option key={cat} value={cat}>{cat}</option>
            ))}
          </select>
        </div>
      </div>

      <div className="books-section">
        <h2>Books ({filteredBooks.length})</h2>
        {filteredBooks.length === 0 ? (
          <div className="no-books">
            <p>No books found</p>
          </div>
        ) : (
          <div className="books-grid">
            {filteredBooks.map(book => (
              <div key={book.id} className="book-card">
                <div className="book-card-header">
                  <h3>{book.title}</h3>
                  <span className="category-badge">{book.category}</span>
                </div>

                <div className="book-card-body">
                  <div className="book-info">
                    <p><strong>Author:</strong> {book.author}</p>
                    <p><strong>ISBN:</strong> {book.isbn}</p>
                    <p><strong>Pages:</strong> {book.pages}</p>
                    <p><strong>Price:</strong> ${book.price}</p>
                    
                    {/* NEW: Quantity control */}
                    <div className="quantity-control">
                      <strong>Quantity:</strong>
                      <div className="quantity-buttons">
                        <button 
                          className="qty-btn decrease"
                          onClick={() => updateQuantity(book.id, (book.quantity || 1) - 1)}
                          disabled={book.quantity <= 1}
                          title="Decrease quantity"
                        >
                          −
                        </button>
                        <span className="quantity-value">{book.quantity || 1}</span>
                        <button 
                          className="qty-btn increase"
                          onClick={() => updateQuantity(book.id, (book.quantity || 1) + 1)}
                          title="Increase quantity"
                        >
                          +
                        </button>
                      </div>
                    </div>
                  </div>
                </div>

                <div className="book-card-footer">
                  <button
                    onClick={() => handleDeleteBook(book.id)}
                    className="delete-btn"
                    title="Delete book"
                  >
                    🗑️ Delete
                  </button>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  )
}

export default Dashboard
