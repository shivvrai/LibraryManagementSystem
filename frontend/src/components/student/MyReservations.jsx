import { useState, useEffect } from 'react'
import { studentAPI } from '../../utils/api'
import { useToast } from '../ui/Toast'

const STATUS_CONFIG = {
  waiting: { label: 'Waiting', color: 'info', icon: '⏳' },
  awaiting_pickup: { label: 'Ready for Pickup', color: 'warning', icon: '📦' },
  fulfilled: { label: 'Fulfilled', color: 'success', icon: '✅' },
  expired: { label: 'Expired', color: 'error', icon: '⏰' },
  cancelled: { label: 'Cancelled', color: 'error', icon: '❌' },
}

const MyReservations = () => {
  const [reservations, setReservations] = useState([])
  const [loading, setLoading] = useState(true)
  const [cancellingId, setCancellingId] = useState(null)
  const toast = useToast()

  useEffect(() => {
    loadReservations()
  }, [])

  const loadReservations = async () => {
    try {
      setLoading(true)
      const data = await studentAPI.getReservations()
      setReservations(data || [])
    } catch (err) {
      console.error('Failed to load reservations:', err)
    } finally {
      setLoading(false)
    }
  }

  const handleCancel = async (reservationId) => {
    setCancellingId(reservationId)
    try {
      await studentAPI.cancelReservation(reservationId)
      toast.success('Reservation cancelled')
      loadReservations()
    } catch (error) {
      toast.error(error.message || 'Failed to cancel reservation')
    } finally {
      setCancellingId(null)
    }
  }

  const getCountdown = (expiresAt) => {
    if (!expiresAt) return null
    const now = new Date()
    const expires = new Date(expiresAt)
    const diff = expires - now
    if (diff <= 0) return 'Expired'
    const hours = Math.floor(diff / 3600000)
    const minutes = Math.floor((diff % 3600000) / 60000)
    return `${hours}h ${minutes}m remaining`
  }

  if (loading) {
    return (
      <div className="my-reservations">
        <div className="loading-placeholder animate-fadeInUp">
          <div className="spinner" style={{ width: 32, height: 32 }} />
          <p>Loading reservations...</p>
        </div>
      </div>
    )
  }

  if (reservations.length === 0) {
    return (
      <div className="my-reservations">
        <div className="empty-state animate-fadeInUp">
          <div className="empty-state__icon">📋</div>
          <h3>No active reservations</h3>
          <p>When a book is out of stock, you can reserve it to join the waitlist.</p>
        </div>
      </div>
    )
  }

  return (
    <div className="my-reservations">
      <h2>My Reservations</h2>
      <div className="reservations-list">
        {reservations.map((res, i) => {
          const config = STATUS_CONFIG[res.status] || STATUS_CONFIG.waiting
          const countdown = res.status === 'awaiting_pickup' ? getCountdown(res.expires_at) : null

          return (
            <div
              key={res.id}
              className={`reservation-card reservation-card--${config.color} animate-fadeInUp`}
              style={{ '--stagger': i }}
            >
              <div className="reservation-card__header">
                <div className="reservation-card__book">
                  <h3>{res.book_title}</h3>
                  <span className={`status-pill status-pill--${config.color}`}>
                    {config.icon} {config.label}
                  </span>
                </div>
                <div className="reservation-card__position">
                  <span className="position-number">#{res.position}</span>
                  <span className="position-label">in queue</span>
                </div>
              </div>

              {/* Timeline visualization */}
              <div className="reservation-timeline">
                <div className={`timeline-step ${res.status === 'waiting' || res.status === 'awaiting_pickup' ? 'active' : 'done'}`}>
                  <div className="timeline-dot" />
                  <span>Waiting</span>
                </div>
                <div className="timeline-line" />
                <div className={`timeline-step ${res.status === 'awaiting_pickup' ? 'active' : res.status === 'fulfilled' ? 'done' : ''}`}>
                  <div className="timeline-dot" />
                  <span>Ready</span>
                </div>
                <div className="timeline-line" />
                <div className={`timeline-step ${res.status === 'fulfilled' ? 'done' : ''}`}>
                  <div className="timeline-dot" />
                  <span>Collected</span>
                </div>
              </div>

              {/* Countdown for awaiting_pickup */}
              {countdown && (
                <div className="reservation-countdown">
                  <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                    <circle cx="12" cy="12" r="10" /><polyline points="12 6 12 12 16 14" />
                  </svg>
                  <span>{countdown} to pick up</span>
                </div>
              )}

              {/* Barcode if assigned */}
              {res.barcode && (
                <div className="reservation-barcode">
                  Reserved copy: <strong>{res.barcode}</strong>
                </div>
              )}

              {/* Actions */}
              <div className="reservation-card__actions">
                {(res.status === 'waiting' || res.status === 'awaiting_pickup') && (
                  <button
                    onClick={() => handleCancel(res.id)}
                    disabled={cancellingId === res.id}
                    className="btn btn-outline-danger btn-sm"
                  >
                    {cancellingId === res.id ? (
                      <><span className="btn-spinner" /> Cancelling...</>
                    ) : (
                      'Cancel Reservation'
                    )}
                  </button>
                )}
                <span className="reservation-date">
                  Reserved on {new Date(res.reserved_at).toLocaleDateString()}
                </span>
              </div>
            </div>
          )
        })}
      </div>
    </div>
  )
}

export default MyReservations
