import { useState } from 'react'

const BookManager = ({ onBookAdded }) => {
  const [showForm, setShowForm] = useState(false)
  const [newBook, setNewBook] = useState({
    title: '',
    author: '',
    pages: '',
    price: '',
    isbn: '',
    category: '',
    quantity: '1'
  })
  const [errors, setErrors] = useState({})
  const [loading, setLoading] = useState(false)

  const validateISBN = (isbn) => {
    const cleanISBN = isbn.replace(/[-\s]/g, '')
    if (cleanISBN.length !== 13 || !/^\d{13}$/.test(cleanISBN)) {
      return false
    }

    let sum = 0
    for (let i = 0; i < 12; i++) {
      sum += parseInt(cleanISBN[i]) * (i % 2 === 0 ? 1 : 3)
    }
    const checkDigit = (10 - (sum % 10)) % 10
    return checkDigit === parseInt(cleanISBN[12])
  }

  const validateForm = () => {
    const newErrors = {}

    if (!newBook.title.trim()) {
      newErrors.title = 'Title is required'
    }

    if (!newBook.author.trim()) {
      newErrors.author = 'Author is required'
    }

    if (!newBook.pages || parseInt(newBook.pages) <= 0) {
      newErrors.pages = 'Valid page count is required'
    }

    if (!newBook.price || parseFloat(newBook.price) <= 0) {
      newErrors.price = 'Valid price is required'
    }

    if (!newBook.quantity || parseInt(newBook.quantity) <= 0) {
      newErrors.quantity = 'Valid quantity is required'
    }

    if (!newBook.isbn.trim()) {
      newErrors.isbn = 'ISBN is required'
    } else if (!validateISBN(newBook.isbn)) {
      newErrors.isbn = 'Invalid ISBN-13 format'
    }

    if (!newBook.category.trim()) {
      newErrors.category = 'Category is required'
    }

    setErrors(newErrors)
    return Object.keys(newErrors).length === 0
  }

  const addBook = async () => {
    if (!validateForm()) return

    setLoading(true)
    try {
      const token = localStorage.getItem('token')
      const response = await fetch('http://localhost:5000/api/books', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${token}`
        },
        body: JSON.stringify({
          ...newBook,
          pages: parseInt(newBook.pages),
          price: parseFloat(newBook.price),
          quantity: parseInt(newBook.quantity)
        })
      })

      const data = await response.json()

      if (response.ok) {
        setNewBook({
          title: '',
          author: '',
          pages: '',
          price: '',
          isbn: '',
          category: '',
          quantity: '1'
        })
        setErrors({})
        setShowForm(false)
        onBookAdded()
      } else {
        setErrors({ general: data.error || 'Failed to add book' })
      }
    } catch (err) {
      setErrors({ general: 'Failed to add book. Please try again.' })
      console.error('Add book error:', err)
    } finally {
      setLoading(false)
    }
  }

  const categories = [
    'Fiction', 'Non-Fiction', 'Science', 'Technology', 'History',
    'Biography', 'Fantasy', 'Romance', 'Mystery', 'Thriller',
    'Science Fiction', 'Horror', 'Poetry', 'Drama', 'Education'
  ]

  return (
    <div className="book-manager">
      <div className="manager-header">
        <h2>Add New Book</h2>
        <button
          onClick={() => setShowForm(!showForm)}
          className="toggle-form-btn"
        >
          {showForm ? '✕ Close' : '+ Add Book'}
        </button>
      </div>

      {showForm && (
        <div className="form-container">
          <div className="form-row">
            <div className="form-group">
              <label htmlFor="title">Title *</label>
              <input
                id="title"
                type="text"
                placeholder="Enter book title"
                value={newBook.title}
                onChange={(e) => setNewBook({...newBook, title: e.target.value})}
                disabled={loading}
              />
              {errors.title && <span className="error">{errors.title}</span>}
            </div>

            <div className="form-group">
              <label htmlFor="author">Author *</label>
              <input
                id="author"
                type="text"
                placeholder="Enter author name"
                value={newBook.author}
                onChange={(e) => setNewBook({...newBook, author: e.target.value})}
                disabled={loading}
              />
              {errors.author && <span className="error">{errors.author}</span>}
            </div>
          </div>

          <div className="form-row">
            <div className="form-group">
              <label htmlFor="pages">Pages *</label>
              <input
                id="pages"
                type="number"
                placeholder="Number of pages"
                value={newBook.pages}
                onChange={(e) => setNewBook({...newBook, pages: e.target.value})}
                disabled={loading}
              />
              {errors.pages && <span className="error">{errors.pages}</span>}
            </div>

            <div className="form-group">
              <label htmlFor="price">Price ($) *</label>
              <input
                id="price"
                type="number"
                step="0.01"
                placeholder="Book price"
                value={newBook.price}
                onChange={(e) => setNewBook({...newBook, price: e.target.value})}
                disabled={loading}
              />
              {errors.price && <span className="error">{errors.price}</span>}
            </div>

            <div className="form-group">
              <label htmlFor="quantity">Quantity *</label>
              <input
                id="quantity"
                type="number"
                placeholder="Quantity"
                value={newBook.quantity}
                onChange={(e) => setNewBook({...newBook, quantity: e.target.value})}
                disabled={loading}
              />
              {errors.quantity && <span className="error">{errors.quantity}</span>}
            </div>
          </div>

          <div className="form-row">
            <div className="form-group">
              <label htmlFor="isbn">ISBN (13 digits) *</label>
              <input
                id="isbn"
                type="text"
                placeholder="e.g., 9780618053267"
                value={newBook.isbn}
                onChange={(e) => setNewBook({...newBook, isbn: e.target.value})}
                disabled={loading}
              />
              {errors.isbn && <span className="error">{errors.isbn}</span>}
            </div>

            <div className="form-group">
              <label htmlFor="category">Category *</label>
              <select
                id="category"
                value={newBook.category}
                onChange={(e) => setNewBook({...newBook, category: e.target.value})}
                disabled={loading}
              >
                <option value="">Select Category</option>
                {categories.map(cat => (
                  <option key={cat} value={cat}>{cat}</option>
                ))}
              </select>
              {errors.category && <span className="error">{errors.category}</span>}
            </div>
          </div>

          {errors.general && (
            <div className="error-message">
              ❌ {errors.general}
            </div>
          )}

          <div className="form-actions">
            <button
              onClick={addBook}
              disabled={loading}
              className="add-book-btn"
            >
              {loading ? '⏳ Adding...' : '✓ Add Book'}
            </button>

            <button
              onClick={() => {
                setShowForm(false)
                setErrors({})
              }}
              disabled={loading}
              className="cancel-btn"
            >
              Cancel
            </button>
          </div>
        </div>
      )}
    </div>
  )
}

export default BookManager
