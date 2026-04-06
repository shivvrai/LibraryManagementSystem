import { useState, useEffect } from 'react'
import { adminAPI } from '../../utils/api'
import './AdminDashboard.css'

export default function TransactionHistory() {
  const [transactions, setTransactions] = useState([])
  const [loading, setLoading] = useState(true)
  const [filter, setFilter] = useState('all')

  useEffect(() => {
    loadTransactions()
  }, [])

  const loadTransactions = async () => {
    try {
      setLoading(true)
      const data = await adminAPI.getTransactions()
      setTransactions(data)
    } catch (error) {
      console.error('Failed to load transactions:', error)
      alert('Failed to load transaction history')
    } finally {
      setLoading(false)
    }
  }

  const filteredTransactions = transactions.filter(t => {
    if (filter === 'all') return true
    return t.status === filter
  })

  if (loading) {
    return <div className="loading">Loading transactions...</div>
  }

  return (
    <div className="transactions-section">
      <div className="manager-header">
        <h2>Transaction History</h2>
        <div className="filter-buttons">
          <button 
            className={`btn ${filter === 'all' ? 'btn-primary' : 'btn-secondary'}`}
            onClick={() => setFilter('all')}
          >
            All ({transactions.length})
          </button>
          <button 
            className={`btn ${filter === 'borrowed' ? 'btn-primary' : 'btn-secondary'}`}
            onClick={() => setFilter('borrowed')}
          >
            Active ({transactions.filter(t => t.status === 'borrowed').length})
          </button>
          <button 
            className={`btn ${filter === 'returned' ? 'btn-primary' : 'btn-secondary'}`}
            onClick={() => setFilter('returned')}
          >
            Returned ({transactions.filter(t => t.status === 'returned').length})
          </button>
        </div>
      </div>

      {filteredTransactions.length === 0 ? (
        <div className="empty-state">No transactions found</div>
      ) : (
        <div className="table-container">
          <table className="transactions-table">
            <thead>
              <tr>
                <th>ID</th>
                <th>Student</th>
                <th>Book</th>
                <th>Borrow Date</th>
                <th>Due Date</th>
                <th>Return Date</th>
                <th>Status</th>
                <th>Fine</th>
              </tr>
            </thead>
            <tbody>
              {filteredTransactions.map(transaction => (
                <tr key={transaction.id}>
                  <td>{transaction.id}</td>
                  <td>{transaction.student_name}</td>
                  <td>{transaction.book_title}</td>
                  <td>{new Date(transaction.borrow_date).toLocaleDateString()}</td>
                  <td>{new Date(transaction.due_date).toLocaleDateString()}</td>
                  <td>
                    {transaction.return_date 
                      ? new Date(transaction.return_date).toLocaleDateString() 
                      : '-'
                    }
                  </td>
                  <td>
                    <span className={`status status-${transaction.status}`}>
                      {transaction.status}
                    </span>
                  </td>
                  <td>{transaction.fine > 0 ? `₹${transaction.fine}` : '-'}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  )
}
