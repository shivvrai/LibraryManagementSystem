import { useState, useMemo, useRef, useEffect } from 'react'
import BookCard from './BookCard'
import { BookCardSkeleton } from '../ui/Skeleton'

const BrowseBooks = ({ books, fines, onBorrow, loading = false }) => {
  const [searchQuery, setSearchQuery] = useState('')
  const [selectedCategory, setSelectedCategory] = useState('all')
  const [showSuggestions, setShowSuggestions] = useState(false)
  const searchRef = useRef(null)

  // Close suggestions on outside click
  useEffect(() => {
    const handler = (e) => {
      if (searchRef.current && !searchRef.current.contains(e.target)) {
        setShowSuggestions(false)
      }
    }
    document.addEventListener('mousedown', handler)
    return () => document.removeEventListener('mousedown', handler)
  }, [])

  // Extract unique categories
  const categories = useMemo(() => {
    const cats = [...new Set(books.map(b => b.category))].sort()
    return ['all', ...cats]
  }, [books])

  // Top-5 search suggestions
  const suggestions = useMemo(() => {
    if (!searchQuery.trim() || searchQuery.length < 2) return []
    const q = searchQuery.toLowerCase()
    return books
      .filter(b =>
        b.title.toLowerCase().includes(q) ||
        b.author.toLowerCase().includes(q) ||
        b.isbn.includes(q)
      )
      .slice(0, 5)
  }, [books, searchQuery])

  // Filter books by search and category
  const filteredBooks = useMemo(() => {
    return books.filter(book => {
      const matchesSearch = !searchQuery ||
        book.title.toLowerCase().includes(searchQuery.toLowerCase()) ||
        book.author.toLowerCase().includes(searchQuery.toLowerCase()) ||
        book.isbn.includes(searchQuery)
      const matchesCategory = selectedCategory === 'all' || book.category === selectedCategory
      return matchesSearch && matchesCategory
    })
  }, [books, searchQuery, selectedCategory])

  if (loading) {
    return (
      <div className="browse-books">
        <h2>Available Books</h2>
        <div className="books-grid">
          {Array.from({ length: 6 }).map((_, i) => (
            <BookCardSkeleton key={i} />
          ))}
        </div>
      </div>
    )
  }

  return (
    <div className="browse-books">
      <div className="browse-header">
        <h2>Available Books</h2>
        <span className="browse-count">{filteredBooks.length} books</span>
      </div>

      {/* Search bar with suggestions */}
      <div className="browse-search-bar" ref={searchRef} style={{ position: 'relative' }}>
        <svg className="search-icon" width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
          <circle cx="11" cy="11" r="8" /><line x1="21" y1="21" x2="16.65" y2="16.65" />
        </svg>
        <input
          type="text"
          placeholder="Search by title, author, or ISBN..."
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

        {/* Suggestions dropdown */}
        {showSuggestions && suggestions.length > 0 && (
          <div className="search-suggestions-dropdown">
            {suggestions.map(book => (
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

      {/* Category filters */}
      <div className="category-filters">
        {categories.map(cat => (
          <button
            key={cat}
            className={`category-pill ${selectedCategory === cat ? 'active' : ''}`}
            onClick={() => setSelectedCategory(cat)}
          >
            {cat === 'all' ? '📚 All' : cat}
          </button>
        ))}
      </div>

      {/* Book grid */}
      {filteredBooks.length === 0 ? (
        <div className="empty-state animate-fadeInUp">
          <div className="empty-state__icon">🔍</div>
          <h3>No books found</h3>
          <p>Try adjusting your search or filter</p>
        </div>
      ) : (
        <div className="books-grid">
          {filteredBooks.map((book, i) => (
            <BookCard
              key={book.id}
              book={book}
              index={i}
              onBorrow={onBorrow}
              onReserve={onBorrow}
              borrowDisabled={fines.borrowed_books >= 3}
            />
          ))}
        </div>
      )}
    </div>
  )
}

export default BrowseBooks
