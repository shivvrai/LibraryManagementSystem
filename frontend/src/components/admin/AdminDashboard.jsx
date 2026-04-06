import { useState, useEffect } from 'react'
import { adminAPI } from '../../utils/api'
import { useToast } from '../ui/Toast'
import BookManager from './BookManager'
import StudentManagement from './StudentManagement'
import TransactionHistory from './TransactionHistory'
import OverdueBooks from './OverdueBooks'
import ReservationQueue from './ReservationQueue'
import AdminSettings from './AdminSettings'
import ThemeToggle from '../ui/ThemeToggle'
import './AdminDashboard.css'
import '../student/StudentDashboard.css'

const AdminDashboard = ({ onLogout }) => {
  const [activeTab, setActiveTab] = useState('books')
  const [stats, setStats] = useState(null)
  const [books, setBooks] = useState([])
  const [students, setStudents] = useState([])
  const [transactions, setTransactions] = useState([])
  const [overdueBooks, setOverdueBooks] = useState([])
  const toast = useToast()

  useEffect(() => {
    loadData()
  }, [])

  const loadData = async () => {
    try {
      const [statsData, booksData, studentsData, transactionsData, overdueData] = await Promise.all([
        adminAPI.getStats(),
        adminAPI.getBooks(),
        adminAPI.getStudents(),
        adminAPI.getTransactions(),
        adminAPI.getOverdue()
      ])
      
      setStats(statsData)
      setBooks(booksData)
      setStudents(studentsData)
      setTransactions(transactionsData)
      setOverdueBooks(overdueData)
    } catch (err) {
      console.error('Failed to load data:', err)
      toast.error('Failed to load dashboard data')
    }
  }

  const statCards = stats ? [
    { label: 'Total Books', value: stats.total_books, icon: '📚', bg: 'var(--color-bg-1)' },
    { label: 'Total Students', value: stats.total_students, icon: '👥', bg: 'var(--color-bg-5)' },
    { label: 'Active Borrows', value: stats.active_borrows, icon: '📖', bg: 'var(--color-bg-3)' },
    { label: 'Overdue Books', value: stats.overdue_books, icon: '⚠️', bg: 'var(--color-bg-4)' },
    { label: 'Total Fines', value: `₹${stats.total_fines}`, icon: '💰', bg: 'var(--color-bg-2)' },
    { label: 'Transactions', value: stats.total_transactions, icon: '📋', bg: 'var(--color-bg-8)' },
  ] : []

  const tabs = [
    { id: 'books', label: 'Books', icon: '📚' },
    { id: 'students', label: 'Students', icon: '👥' },
    { id: 'transactions', label: 'Transactions', icon: '📋' },
    { id: 'overdue', label: 'Overdue', icon: '⚠️', badge: overdueBooks.length || null },
    { id: 'reservations', label: 'Reservations', icon: '🔔' },
    { id: 'settings', label: 'Settings', icon: '⚙️' },
  ]

  return (
    <div className="admin-dashboard sd-layout">
      {/* ── Sidebar ── */}
      <aside className="sd-sidebar sd-sidebar--admin">
        <div className="sd-sidebar__brand">
          <span className="sd-sidebar__brand-icon">📚</span>
          <div>
            <div className="sd-sidebar__brand-name">LibraryMS</div>
            <div className="sd-sidebar__brand-sub">Admin Panel</div>
          </div>
        </div>

        <div className="sd-sidebar__user">
          <div className="sd-sidebar__avatar sd-sidebar__avatar--admin">A</div>
          <div className="sd-sidebar__user-info">
            <div className="sd-sidebar__user-name">Admin</div>
            <div className="sd-sidebar__user-role">Administrator</div>
          </div>
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
        <button onClick={onLogout} className="sd-sidebar__logout">
          <span>🚪</span> Logout
        </button>
      </aside>

      {/* ── Main content ── */}
      <div className="sd-main">
        {/* Stat cards at the top of the content area */}
        {stats && (
          <div className="stats-grid admin-stats-bar">
            {statCards.map((card, i) => (
              <div
                key={card.label}
                className="stat-card animate-fadeInUp"
                style={{ '--stagger': i, background: card.bg }}
              >
                <span className="stat-card__icon">{card.icon}</span>
                <div className="stat-card__content">
                  <h3 className="stat-card__value">{card.value}</h3>
                  <p className="stat-card__label">{card.label}</p>
                </div>
              </div>
            ))}
          </div>
        )}

        <main className="sd-content">
          {activeTab === 'books' && <BookManager books={books} onDataChanged={loadData} />}
          {activeTab === 'students' && <StudentManagement />}
          {activeTab === 'transactions' && <TransactionHistory transactions={transactions} onDataChanged={loadData} />}
          {activeTab === 'overdue' && <OverdueBooks overdueBooks={overdueBooks} onDataChanged={loadData} />}
          {activeTab === 'reservations' && <ReservationQueue />}
          {activeTab === 'settings' && <AdminSettings />}
        </main>
      </div>
    </div>
  )
}

export default AdminDashboard
