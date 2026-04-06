import { useState, useEffect } from 'react'
import { adminAPI } from '../../utils/api'
import './AdminDashboard.css'

export default function OverdueBooks() {
  const [overdueList, setOverdueList] = useState([])
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    loadOverdueBooks()
  }, [])

  const loadOverdueBooks = async () => {
    try {
      setLoading(true)
      const data = await adminAPI.getOverdue()
      setOverdueList(data)
    } catch (error) {
      console.error('Failed to load overdue books:', error)
      alert('Failed to load overdue books')
    } finally {
      setLoading(false)
    }
  }

  const handleReturn = async (transactionId) => {
    if (!confirm('Process return for this overdue book?')) return
    
    try {
      await adminAPI.processReturn(transactionId)
      alert('Book returned successfully')
      loadOverdueBooks()
    } catch (error) {
      console.error('Failed to process return:', error)
      alert('Failed to process return')
    }
  }

  if (loading) {
    return <div className="loading">Loading overdue books...</div>
  }

  return (
    <div className="transactions-section">
      <div className="manager-header">
        <h2>Overdue Books</h2>
        <span className="badge" style={{ fontSize: '1rem', padding: '0.5rem 1rem' }}>
          {overdueList.length} Overdue
        </span>
      </div>

      {overdueList.length === 0 ? (
        <div className="empty-state">
          🎉 No overdue books! All books returned on time.
        </div>
      ) : (
        <div className="table-container">
          <table className="transactions-table">
            <thead>
              <tr>
                <th>Student</th>
                <th>Book</th>
                <th>Due Date</th>
                <th>Days Overdue</th>
                <th>Fine</th>
                <th>Action</th>
              </tr>
            </thead>
            <tbody>
              {overdueList.map(item => (
                <tr key={item.transaction_id}>
                  <td>
                    <div>{item.student_name}</div>
                    <small>{item.student_id}</small>
                  </td>
                  <td>{item.book_title}</td>
                  <td>{new Date(item.due_date).toLocaleDateString()}</td>
                  <td className="text-error">{item.days_overdue} days</td>
                  <td className="text-error">₹{item.fine}</td>
                  <td>
                    <button
                      className="btn btn-sm btn-primary"
                      onClick={() => handleReturn(item.transaction_id)}
                    >
                      Process Return
                    </button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  )
}
