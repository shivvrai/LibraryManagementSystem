import { useState, useMemo, useRef, useEffect } from 'react'
import { adminAPI } from '../../utils/api'
import { useToast } from '../ui/Toast'

const BookManager = ({ books, onDataChanged }) => {
  const toast = useToast()
  const [showForm, setShowForm] = useState(false)
  const [searchQuery, setSearchQuery] = useState('')
  const [showSuggestions, setShowSuggestions] = useState(false)
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
  const [showAuthorSuggestions, setShowAuthorSuggestions] = useState(false)
  const authorRef = useRef(null)
  const searchRef = useRef(null)

  const categories = [
    'Fiction', 'Non-Fiction', 'Science', 'Technology', 'History',
    'Biography', 'Fantasy', 'Romance', 'Mystery', 'Thriller'
  ]

  // Unique authors from existing books
  const existingAuthors = useMemo(() => {
    return [...new Set(books.map(b => b.author))].sort()
  }, [books])

  // Filtered author suggestions
  const authorSuggestions = useMemo(() => {
    if (!newBook.author.trim()) return existingAuthors.slice(0, 5)
    const q = newBook.author.toLowerCase()
    return existingAuthors.filter(a => a.toLowerCase().includes(q)).slice(0, 5)
  }, [newBook.author, existingAuthors])

  // Top-5 search suggestions
  const searchSuggestions = useMemo(() => {
    if (!searchQuery.trim() || searchQuery.length < 2) return []
    const q = searchQuery.toLowerCase()
    return books
      .filter(b =>
        b.title.toLowerCase().includes(q) ||
        b.author.toLowerCase().includes(q) ||
        b.isbn?.includes(q) ||
        b.category?.toLowerCase().includes(q)
      )
      .slice(0, 5)
  }, [books, searchQuery])

  // Filtered book list
  const filteredBooks = useMemo(() => {
    if (!searchQuery.trim()) return books
    const q = searchQuery.toLowerCase()
    return books.filter(b =>
      b.title.toLowerCase().includes(q) ||
      b.author.toLowerCase().includes(q) ||
      b.isbn?.includes(q) ||
      b.category?.toLowerCase().includes(q)
    )
  }, [books, searchQuery])

  // Close dropdowns on outside click
  useEffect(() => {
    const handler = (e) => {
      if (authorRef.current && !authorRef.current.contains(e.target)) {
        setShowAuthorSuggestions(false)
      }
      if (searchRef.current && !searchRef.current.contains(e.target)) {
        setShowSuggestions(false)
      }
    }
    document.addEventListener('mousedown', handler)
    return () => document.removeEventListener('mousedown', handler)
  }, [])

  const validateISBN = (isbn) => {
    const cleanISBN = isbn.replace(/[-\s]/g, '')
    return cleanISBN.length === 13 && /^\d{13}$/.test(cleanISBN)
  }

  const validateForm = () => {
    const newErrors = {}
    if (!newBook.title.trim()) newErrors.title = 'Title is required'
    if (!newBook.author.trim()) newErrors.author = 'Author is required'
    if (!newBook.pages || parseInt(newBook.pages) <= 0) newErrors.pages = 'Valid page count is required'
    if (!newBook.price || parseFloat(newBook.price) <= 0) newErrors.price = 'Valid price is required'
    if (!newBook.quantity || parseInt(newBook.quantity) <= 0) newErrors.quantity = 'Valid quantity is required'
    if (!newBook.isbn.trim()) newErrors.isbn = 'ISBN is required'
    else if (!validateISBN(newBook.isbn)) newErrors.isbn = 'Invalid ISBN-13 format'
    if (!newBook.category.trim()) newErrors.category = 'Category is required'
    setErrors(newErrors)
    return Object.keys(newErrors).length === 0
  }

  const addBook = async () => {
    if (!validateForm()) return
    const bookToAdd = {
      ...newBook,
      pages: parseInt(newBook.pages),
      price: parseFloat(newBook.price),
      quantity: parseInt(newBook.quantity)
    }
    setLoading(true)
    try {
      await adminAPI.addBook(bookToAdd)
      setNewBook({ title: '', author: '', pages: '', price: '', isbn: '', category: '', quantity: '1' })
      setErrors({})
      setShowForm(false)
      toast.success('✅ Book added successfully!')
      onDataChanged()
    } catch (err) {
      const errorMessage = err.message || 'Failed to add book'
      setErrors({ general: errorMessage })
      toast.error(`❌ ${errorMessage}`)
    } finally {
      setLoading(false)
    }
  }

  const changeQuantity = async (id, action) => {
    try {
      if (action === 'increase') {
        await adminAPI.increaseBookQty(id, 1)
      } else {
        await adminAPI.decreaseBookQty(id, 1)
      }
      onDataChanged()
    } catch (err) {
      toast.error(err.message || `Failed to ${action} quantity`)
    }
  }

  return (
    <div className="book-manager">
      <div className="manager-header">
        <h2>Books Management</h2>
        <button onClick={() => setShowForm(!showForm)} className="btn btn-primary">
          {showForm ? '✕ Close' : '+ Add Book'}
        </button>
      </div>

      {showForm && (
        <div className="form-container">
          <div className="form-row">
            <div className="form-group">
              <label>Title *</label>
              <input type="text" placeholder="Book title" value={newBook.title} onChange={(e) => setNewBook({...newBook, title: e.target.value})} />
              {errors.title && <span className="error">{errors.title}</span>}
            </div>
            <div className="form-group" ref={authorRef} style={{ position: 'relative' }}>
              <label>Author *</label>
              <input
                type="text"
                placeholder="Author name (type or select)"
                value={newBook.author}
                onChange={(e) => { setNewBook({...newBook, author: e.target.value}); setShowAuthorSuggestions(true) }}
                onFocus={() => setShowAuthorSuggestions(true)}
                autoComplete="off"
              />
              {errors.author && <span className="error">{errors.author}</span>}
              {showAuthorSuggestions && authorSuggestions.length > 0 && (
                <div className="search-suggestions-dropdown" style={{ top: '100%', marginTop: 4 }}>
                  {authorSuggestions.map(author => (
                    <button
                      key={author}
                      className="search-suggestion-item"
                      type="button"
                      onMouseDown={(e) => e.preventDefault()}
                      onClick={() => { setNewBook({...newBook, author}); setShowAuthorSuggestions(false) }}
                    >
                      <span className="suggestion-icon">✍️</span>
                      <span className="suggestion-text">{author}</span>
                    </button>
                  ))}
                </div>
              )}
            </div>
          </div>

          <div className="form-row">
            <div className="form-group">
              <label>Pages *</label>
              <input type="number" placeholder="Pages" value={newBook.pages} onChange={(e) => setNewBook({...newBook, pages: e.target.value})} />
              {errors.pages && <span className="error">{errors.pages}</span>}
            </div>
            <div className="form-group">
              <label>Price (₹) *</label>
              <input type="number" step="0.01" placeholder="Price" value={newBook.price} onChange={(e) => setNewBook({...newBook, price: e.target.value})} />
              {errors.price && <span className="error">{errors.price}</span>}
            </div>
            <div className="form-group">
              <label>Quantity *</label>
              <input type="number" placeholder="Quantity" value={newBook.quantity} onChange={(e) => setNewBook({...newBook, quantity: e.target.value})} />
              {errors.quantity && <span className="error">{errors.quantity}</span>}
            </div>
          </div>

          <div className="form-row">
            <div className="form-group">
              <label>ISBN (13) *</label>
              <input type="text" placeholder="ISBN" value={newBook.isbn} onChange={(e) => setNewBook({...newBook, isbn: e.target.value})} />
              {errors.isbn && <span className="error">{errors.isbn}</span>}
            </div>
            <div className="form-group">
              <label>Category *</label>
              <select value={newBook.category} onChange={(e) => setNewBook({...newBook, category: e.target.value})}>
                <option value="">Select Category</option>
                {categories.map(cat => <option key={cat} value={cat}>{cat}</option>)}
              </select>
              {errors.category && <span className="error">{errors.category}</span>}
            </div>
          </div>

          {errors.general && <div className="error-message">❌ {errors.general}</div>}

          <div className="form-actions">
            <button onClick={addBook} disabled={loading} className="btn btn-success">
              {loading ? 'Adding...' : '✓ Add Book'}
            </button>
            <button onClick={() => setShowForm(false)} className="btn btn-secondary">Cancel</button>
          </div>
        </div>
      )}

      {/* Search bar with suggestions */}
      <div className="browse-search-bar" ref={searchRef} style={{ position: 'relative', marginBottom: '1.25rem' }}>
        <svg className="search-icon" width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
          <circle cx="11" cy="11" r="8" /><line x1="21" y1="21" x2="16.65" y2="16.65" />
        </svg>
        <input
          type="text"
          placeholder="Search books by title, author, ISBN or category..."
          value={searchQuery}
          onChange={(e) => { setSearchQuery(e.target.value); setShowSuggestions(true) }}
          onFocus={() => searchQuery.length >= 2 && setShowSuggestions(true)}
          className="browse-search-input"
        />
        {searchQuery && (
          <button className="search-clear" onClick={() => { setSearchQuery(''); setShowSuggestions(false) }}>
            <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
              <line x1="18" y1="6" x2="6" y2="18" /><line x1="6" y1="6" x2="18" y2="18" />
            </svg>
          </button>
        )}
        {showSuggestions && searchSuggestions.length > 0 && (
          <div className="search-suggestions-dropdown">
            {searchSuggestions.map(book => (
              <button
                key={book.id}
                className="search-suggestion-item"
                onMouseDown={(e) => e.preventDefault()}
                onClick={() => { setSearchQuery(book.title); setShowSuggestions(false) }}
              >
                <span className="suggestion-icon">📖</span>
                <span className="suggestion-text">
                  <strong>{book.title}</strong>
                  <span className="suggestion-sub"> — {book.author} · {book.category}</span>
                </span>
              </button>
            ))}
          </div>
        )}
      </div>
      {searchQuery && (
        <p style={{ color: 'var(--color-text-muted, #888)', fontSize: '0.85rem', marginBottom: '0.75rem' }}>
          Showing {filteredBooks.length} of {books.length} books
        </p>
      )}

      <div className="books-grid">
        {filteredBooks.map(book => (
          <div key={book.id} className="book-card">
            <h3>{book.title}</h3>
            <p className="author">{book.author}</p>
            <p className="meta">Pages: {book.pages} | Price: ₹{book.price}</p>
            <p className="meta">ISBN: {book.isbn}</p>
            <p className="category">Category: {book.category}</p>
            <p className="availability">Available: {book.available} / {book.quantity}</p>
            <div className="quantity-controls" style={{ display: 'flex', gap: '8px', marginTop: '8px' }}>
              <button
                onClick={() => changeQuantity(book.id, 'decrease')}
                className="btn btn-sm btn-danger"
                disabled={book.available <= 0}
                title={book.available <= 0 ? 'All copies are borrowed' : 'Remove 1 copy'}
              >
                ➖ Remove
              </button>
              <button
                onClick={() => changeQuantity(book.id, 'increase')}
                className="btn btn-sm btn-success"
                title="Add 1 copy"
              >
                ➕ Add
              </button>
            </div>
          </div>
        ))}
      </div>
    </div>
  )
}

export default BookManager
