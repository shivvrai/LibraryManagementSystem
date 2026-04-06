import { useState } from 'react'
import { studentAPI } from '../../utils/api'
import { useToast } from '../ui/Toast'

const COVER_GRADIENTS = [
  'linear-gradient(135deg, #667eea 0%, #764ba2 100%)',
  'linear-gradient(135deg, #f093fb 0%, #f5576c 100%)',
  'linear-gradient(135deg, #4facfe 0%, #00f2fe 100%)',
  'linear-gradient(135deg, #43e97b 0%, #38f9d7 100%)',
  'linear-gradient(135deg, #fa709a 0%, #fee140 100%)',
  'linear-gradient(135deg, #a18cd1 0%, #fbc2eb 100%)',
  'linear-gradient(135deg, #fccb90 0%, #d57eeb 100%)',
  'linear-gradient(135deg, #e0c3fc 0%, #8ec5fc 100%)',
]

const BookCard = ({ book, onBorrow, onReserve, borrowDisabled, index = 0 }) => {
  const [borrowing, setBorrowing] = useState(false)
  const [reserving, setReserving] = useState(false)
  const toast = useToast()
  const gradient = COVER_GRADIENTS[book.id % COVER_GRADIENTS.length]

  const getAvailabilityBadge = () => {
    if (book.available <= 0) {
      return <span className="availability-badge out-of-stock">Out of Stock</span>
    }
    if (book.available <= 2) {
      return <span className="availability-badge low-stock">Low Stock ({book.available} left)</span>
    }
    return <span className="availability-badge in-stock">In Stock ({book.available})</span>
  }

  const handleBorrow = async () => {
    setBorrowing(true)
    try {
      const res = await studentAPI.borrowBook(book.id)
      toast.success(res.message || `Borrowed "${book.title}" successfully!`)
      onBorrow?.()
    } catch (error) {
      toast.error(error.message || 'Failed to borrow book')
    } finally {
      setBorrowing(false)
    }
  }

  const handleReserve = async () => {
    setReserving(true)
    try {
      const res = await studentAPI.reserveBook(book.id)
      toast.success(res.message || 'Added to waitlist!')
      onReserve?.()
    } catch (error) {
      toast.error(error.message || 'Failed to reserve book')
    } finally {
      setReserving(false)
    }
  }



  return (
    <div className="book-card animate-fadeInUp" style={{ '--stagger': index }}>
      {/* Cover placeholder */}
      <div className="book-card__cover" style={{ background: gradient }}>
        <div className="book-card__cover-content">
          <span className="book-card__cover-title">{book.title}</span>
          <span className="book-card__cover-author">{book.author}</span>
        </div>
        <div className="book-card__badges">
          {getAvailabilityBadge()}
          <span className="category-badge">{book.category}</span>
        </div>
      </div>

      {/* Info section */}
      <div className="book-card__body">
        <h3 className="book-card__title">{book.title}</h3>
        <p className="book-card__author">by {book.author}</p>
        <div className="book-card__meta">
          <span>{book.pages} pages</span>
          <span className="meta-dot">·</span>
          <span>₹{book.price}</span>
          <span className="meta-dot">·</span>
          <span className="book-card__isbn">{book.isbn}</span>
        </div>
      </div>

      {/* Actions */}
      <div className="book-card__actions">
        {book.available > 0 ? (
          <button
            onClick={handleBorrow}
            disabled={borrowDisabled || borrowing}
            className="btn btn-primary book-card__btn"
          >
            {borrowing ? (
              <><span className="btn-spinner" /> Borrowing...</>
            ) : (
              '📚 Borrow'
            )}
          </button>
        ) : (
          <button
            onClick={handleReserve}
            disabled={reserving}
            className="btn btn-reserve book-card__btn"
          >
            {reserving ? (
              <><span className="btn-spinner" /> Reserving...</>
            ) : (
              '🔔 Reserve / Waitlist'
            )}
          </button>
        )}

      </div>
    </div>
  )
}

export default BookCard
