import { useState, useEffect } from 'react'
import { logout, getUser } from '../../utils/auth'
import { studentAPI } from '../../utils/api'
import { formatDate, calculateDaysRemaining, getDueDateStatus } from '../../utils/dateUtils'
import BrowseBooks from './BrowseBooks'
import MyBooks from './MyBooks'
import MyReservations from './MyReservations'
import NotificationBell from './NotificationBell'
import PreferencesPanel from './PreferencesPanel'
import PersonalizedWelcome from './PersonalizedWelcome'
import StudentSettings from './StudentSettings'
import ThemeToggle from '../ui/ThemeToggle'
import './StudentDashboard.css'

const StudentDashboard = ({ onLogout }) => {
  const [availableBooks, setAvailableBooks] = useState([])
  const [myBooks, setMyBooks] = useState([])
  const [fines, setFines] = useState({ fine_amount: 0, borrowed_books: 0 })
  const [reservationCount, setReservationCount] = useState(0)
  const [preferencesCount, setPreferencesCount] = useState(0)
  const [unreadNotifications, setUnreadNotifications] = useState(0)
  const [activeTab, setActiveTab] = useState('browse')
  const [loading, setLoading] = useState(true)
  const user = getUser()

  useEffect(() => {
    loadData()
  }, [])

  const loadData = async () => {
    try {
      setLoading(true)
      const [books, borrowed, fineData, prefsData, notifData, reservations] = await Promise.all([
        studentAPI.getBooks(),
        studentAPI.getMyBooks(),
        studentAPI.getFines(),
        studentAPI.getPreferences().catch(() => ({ preferences: [] })),
        studentAPI.getUnreadCount().catch(() => ({ unread_count: 0 })),
        studentAPI.getReservations().catch(() => []),
      ])
      setAvailableBooks(books)
      setMyBooks(borrowed)
      setFines(fineData)
      setPreferencesCount(prefsData.preferences?.length || 0)
      setUnreadNotifications(notifData.unread_count || 0)
      setReservationCount(Array.isArray(reservations) ? reservations.length : 0)
    } catch (error) {
      console.error('Failed to load data:', error)
    } finally {
      setLoading(false)
    }
  }

  const handleLogout = () => {
    logout()
    onLogout()
  }

  if (loading) {
    return (
      <div className="student-dashboard">
        <div className="loading-placeholder" style={{ minHeight: '100vh', display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
          <div className="spinner" />
        </div>
      </div>
    )
  }

  const tabs = [
    { id: 'browse', label: 'Browse Books', icon: '🔍', badge: null },
    { id: 'my-books', label: 'My Books', icon: '📖', badge: myBooks.length || null },
    { id: 'reservations', label: 'Reservations', icon: '📋', badge: reservationCount || null },
    { id: 'preferences', label: 'Preferences', icon: '🎯', badge: preferencesCount || null },
    { id: 'settings', label: 'Settings', icon: '⚙️', badge: null },
  ]

  return (
    <div className="student-dashboard sd-layout">
      {/* ── Sidebar ── */}
      <aside className="sd-sidebar">
        <div className="sd-sidebar__brand">
          <span className="sd-sidebar__brand-icon">📚</span>
          <div>
            <div className="sd-sidebar__brand-name">My Library</div>
            <div className="sd-sidebar__brand-sub">Student Portal</div>
          </div>
        </div>

        <div className="sd-sidebar__user">
          <div className="sd-sidebar__avatar">{user?.name?.charAt(0).toUpperCase() || '?'}</div>
          <div className="sd-sidebar__user-info">
            <div className="sd-sidebar__user-name">{user?.name?.split(' ')[0]}</div>
            <div className="sd-sidebar__user-role">Student</div>
          </div>
          <NotificationBell />
        </div>

        <nav className="sd-sidebar__nav">
          {tabs.map(tab => (
            <button
              key={tab.id}
              className={`sd-nav-btn ${activeTab === tab.id ? 'active' : ''}`}
              onClick={() => setActiveTab(tab.id)}
            >
              <span className="sd-nav-icon">{tab.icon}</span>
              <span className="sd-nav-label">{tab.label}</span>
              {tab.badge > 0 && <span className="tab-badge">{tab.badge}</span>}
            </button>
          ))}
        </nav>

        <div className="sd-sidebar__bottom-actions">
          <ThemeToggle />
        </div>
        <button onClick={handleLogout} className="sd-sidebar__logout">
          <span>🚪</span> Logout
        </button>
      </aside>

      {/* ── Main area ── */}
      <div className="sd-main">
        <PersonalizedWelcome
          user={user}
          fines={fines}
          preferencesCount={preferencesCount}
          notificationCount={unreadNotifications}
          reservationCount={reservationCount}
        />

        <main className="sd-content">
          {activeTab === 'browse' && (
            <BrowseBooks books={availableBooks} fines={fines} onBorrow={loadData} loading={false} />
          )}
          {activeTab === 'my-books' && (
            <MyBooks books={myBooks} onReturn={loadData} />
          )}
          {activeTab === 'reservations' && <MyReservations />}
          {activeTab === 'preferences' && <PreferencesPanel />}
          {activeTab === 'settings' && <StudentSettings />}
        </main>
      </div>
    </div>
  )
}

export default StudentDashboard
