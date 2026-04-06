import { useState } from 'react'
import { studentAPI } from '../../utils/api'
import { useToast } from '../ui/Toast'
import { formatDate, calculateDaysRemaining, getDueDateStatus } from '../../utils/dateUtils'

const MyBooks = ({ books, onReturn }) => {
  const [returningId, setReturningId] = useState(null)
  const [renewingId, setRenewingId] = useState(null)
  const toast = useToast()

  const handleReturn = async (transactionId) => {
    setReturningId(transactionId)
    try {
      const res = await studentAPI.returnBook(transactionId)
      toast.success(res.message || 'Book returned successfully!')
      if (res.fine > 0) {
        toast.warning(`Fine of ₹${res.fine} charged for ${res.days_overdue} day(s) overdue`)
      }
      onReturn()
    } catch (error) {
      toast.error(error.message || 'Failed to return book')
    } finally {
      setReturningId(null)
    }
  }

  const handleRenew = async (transactionId) => {
    setRenewingId(transactionId)
    try {
      const res = await studentAPI.renewBook(transactionId)
      toast.success(res.message || 'Book renewed successfully!')
      onReturn() // reload data
    } catch (error) {
      toast.error(error.message || 'Failed to renew book')
    } finally {
      setRenewingId(null)
    }
  }

  if (books.length === 0) {
    return (
      <div className="my-books">
        <div className="empty-state animate-fadeInUp">
          <div className="empty-state__icon">📚</div>
          <h3>No borrowed books</h3>
          <p>Browse the catalog and borrow your first book!</p>
        </div>
      </div>
    )
  }

  return (
    <div className="my-books">
      <h2>My Borrowed Books</h2>
      <div className="borrowed-books-list">
        {books.map((item, i) => {
          const daysLeft = calculateDaysRemaining(item.due_date)
          const status = getDueDateStatus(daysLeft)
          const maxRenewals = item.max_renewals || 2
          const renewalCount = item.renewal_count || 0
          const canRenew = renewalCount < maxRenewals
          const totalDays = 7 * (renewalCount + 1)
          const elapsed = totalDays - daysLeft
          const progressPct = Math.min(100, Math.max(0, (elapsed / totalDays) * 100))

          return (
            <div
              key={item.transaction_id}
              className={`borrowed-book-card status-${status} animate-fadeInUp`}
              style={{ '--stagger': i }}
            >
              <div className="book-info">
                <h3>{item.book?.title}</h3>
                <p className="author">by {item.book?.author}</p>
                {item.barcode && (
                  <span className="barcode-badge">
                    <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                      <rect x="3" y="3" width="18" height="18" rx="2" ry="2" />
                      <line x1="7" y1="7" x2="7" y2="17" /><line x1="10" y1="7" x2="10" y2="17" />
                      <line x1="14" y1="7" x2="14" y2="17" /><line x1="17" y1="7" x2="17" y2="17" />
                    </svg>
                    {item.barcode}
                  </span>
                )}
              </div>

              <div className="due-info">
                <div className="due-dates">
                  <p><strong>Borrowed:</strong> {formatDate(item.borrow_date)}</p>
                  <p><strong>Due:</strong> {formatDate(item.due_date)}</p>
                </div>

                {/* Progress bar */}
                <div className="due-progress-bar">
                  <div
                    className={`due-progress-fill progress-${status}`}
                    style={{ width: `${progressPct}%` }}
                  />
                </div>

                <p className={`days-remaining ${status}`}>
                  {daysLeft >= 0
                    ? `${daysLeft} days remaining`
                    : `${Math.abs(daysLeft)} days overdue`
                  }
                </p>
                {item.fine > 0 && (
                  <p className="fine-badge">💰 Fine: ₹{item.fine}</p>
                )}
              </div>

              <div className="borrowed-book-actions">
                {/* Renew button */}
                <button
                  onClick={() => handleRenew(item.transaction_id)}
                  disabled={!canRenew || renewingId === item.transaction_id}
                  className="btn btn-renew"
                  title={!canRenew ? `Max ${maxRenewals} renewals reached` : 'Extend due date'}
                >
                  {renewingId === item.transaction_id ? (
                    <><span className="btn-spinner" /> Renewing...</>
                  ) : (
                    <>🔄 Renew</>
                  )}
                  <span className="renewal-badge">{renewalCount}/{maxRenewals}</span>
                </button>

                {/* Return button */}
                <button
                  onClick={() => handleReturn(item.transaction_id)}
                  disabled={returningId === item.transaction_id}
                  className="btn btn-success"
                >
                  {returningId === item.transaction_id ? (
                    <><span className="btn-spinner" /> Returning...</>
                  ) : (
                    '✓ Return'
                  )}
                </button>
              </div>
            </div>
          )
        })}
      </div>
    </div>
  )
}

export default MyBooks
