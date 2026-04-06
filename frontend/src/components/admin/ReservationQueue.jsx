import { useState, useEffect } from 'react'
import { adminAPI } from '../../utils/api'
import { useToast } from '../ui/Toast'

const STATUS_STYLES = {
  waiting: { bg: 'var(--color-bg-1)', color: 'var(--color-primary)', label: '⏳ Waiting' },
  awaiting_pickup: { bg: 'var(--color-bg-2)', color: 'var(--color-warning)', label: '📦 Awaiting Pickup' },
  fulfilled: { bg: 'var(--color-bg-3)', color: 'var(--color-success)', label: '✅ Fulfilled' },
  expired: { bg: 'var(--color-bg-4)', color: 'var(--color-error)', label: '⏰ Expired' },
  cancelled: { bg: 'var(--color-bg-4)', color: 'var(--color-error)', label: '❌ Cancelled' },
}

const ReservationQueue = () => {
  const [reservations, setReservations] = useState([])
  const [loading, setLoading] = useState(true)
  const toast = useToast()

  useEffect(() => {
    loadReservations()
  }, [])

  const loadReservations = async () => {
    try {
      setLoading(true)
      const data = await adminAPI.getReservations()
      setReservations(data || [])
    } catch (err) {
      toast.error('Failed to load reservations')
    } finally {
      setLoading(false)
    }
  }

  if (loading) {
    return (
      <div className="reservation-queue">
        <div className="loading-placeholder">
          <div className="spinner" style={{ width: 32, height: 32 }} />
          <p>Loading reservations...</p>
        </div>
      </div>
    )
  }

  if (reservations.length === 0) {
    return (
      <div className="reservation-queue">
        <div className="empty-state animate-fadeInUp">
          <div className="empty-state__icon">📋</div>
          <h3>No active reservations</h3>
          <p>All books are available — no students are waiting.</p>
        </div>
      </div>
    )
  }

  return (
    <div className="reservation-queue">
      <div className="section-header">
        <h2>Reservation Queue</h2>
        <span className="section-count">{reservations.length} active</span>
      </div>
      <div className="table-container">
        <table className="data-table">
          <thead>
            <tr>
              <th>Book</th>
              <th>Student</th>
              <th>Position</th>
              <th>Status</th>
              <th>Reserved</th>
              <th>Expires</th>
              <th>Copy</th>
            </tr>
          </thead>
          <tbody>
            {reservations.map((res, i) => {
              const style = STATUS_STYLES[res.status] || STATUS_STYLES.waiting
              return (
                <tr key={res.id} className="animate-fadeInUp" style={{ '--stagger': i }}>
                  <td className="cell-primary">{res.book_title}</td>
                  <td>{res.student_name}</td>
                  <td><span className="position-badge">#{res.position}</span></td>
                  <td>
                    <span className="status-pill" style={{ background: style.bg, color: style.color }}>
                      {style.label}
                    </span>
                  </td>
                  <td className="cell-date">{res.reserved_at ? new Date(res.reserved_at).toLocaleDateString() : '—'}</td>
                  <td className="cell-date">
                    {res.expires_at ? new Date(res.expires_at).toLocaleString() : '—'}
                  </td>
                  <td>
                    {res.barcode ? (
                      <span className="barcode-badge">{res.barcode}</span>
                    ) : '—'}
                  </td>
                </tr>
              )
            })}
          </tbody>
        </table>
      </div>
    </div>
  )
}

export default ReservationQueue
