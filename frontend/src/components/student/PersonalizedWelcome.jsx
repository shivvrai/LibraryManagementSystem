const PersonalizedWelcome = ({ user, fines, preferencesCount, notificationCount, reservationCount = 0 }) => {
  const getGreeting = () => {
    const hour = new Date().getHours()
    if (hour < 12) return 'Good morning'
    if (hour < 17) return 'Good afternoon'
    return 'Good evening'
  }

  const getMotivationalMessage = () => {
    if (fines.borrowed_books === 0) {
      return "Ready to discover your next great read? Browse our collection!"
    }
    if (fines.borrowed_books >= 3) {
      return "You're at your borrow limit! Return a book to borrow more."
    }
    return `You have ${fines.borrowed_books} book${fines.borrowed_books > 1 ? 's' : ''} — happy reading!`
  }

  const stats = [
    { value: fines.borrowed_books, label: 'Borrowed', highlight: false },
    { value: reservationCount, label: 'Reserved', highlight: reservationCount > 0 },
    { value: notificationCount || 0, label: 'Notifications', highlight: notificationCount > 0 },
    { value: `₹${fines.fine_amount}`, label: 'Fines', highlight: fines.fine_amount > 0, warning: fines.fine_amount > 0 },
  ]

  return (
    <div className="personalized-welcome animate-fadeInUp">
      <div className="welcome-content">
        <div className="welcome-text">
          <h2 className="welcome-greeting">
            {getGreeting()}, <span className="welcome-name">{user?.name?.split(' ')[0] || 'Reader'}</span>! 👋
          </h2>
          <p className="welcome-message">{getMotivationalMessage()}</p>
        </div>

        <div className="welcome-quick-stats">
          {stats.map((stat, i) => (
            <div key={stat.label} style={{ display: 'contents' }}>
              {i > 0 && <div className="quick-stat-divider" />}
              <div className={`quick-stat ${stat.highlight ? 'highlight' : ''} ${stat.warning ? 'warning' : ''}`}>
                <span className={`quick-stat-value ${stat.warning ? 'warning' : ''}`}>{stat.value}</span>
                <span className="quick-stat-label">{stat.label}</span>
              </div>
            </div>
          ))}
        </div>
      </div>

      {preferencesCount === 0 && (
        <div className="welcome-cta">
          <span className="cta-icon">🎯</span>
          <span className="cta-text">Set up your book preferences to receive personalized notifications!</span>
        </div>
      )}
    </div>
  )
}

export default PersonalizedWelcome
