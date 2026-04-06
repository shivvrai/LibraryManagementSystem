import { useState, useEffect } from 'react'
import { studentAPI } from '../../utils/api'

const PREFERENCE_TYPES = [
  { value: 'category', label: '📂 Category/Genre', placeholder: 'e.g. Fantasy, Fiction, Science...' },
  { value: 'author', label: '✍️ Author', placeholder: 'e.g. J.K. Rowling, Tolkien...' },
  { value: 'title', label: '📖 Book Title', placeholder: 'e.g. Harry Potter, The Hobbit...' },
]

const PreferencesPanel = () => {
  const [preferences, setPreferences] = useState([])
  const [loading, setLoading] = useState(true)
  const [adding, setAdding] = useState(false)
  const [selectedType, setSelectedType] = useState('category')
  const [value, setValue] = useState('')
  const [error, setError] = useState('')
  const [success, setSuccess] = useState('')

  useEffect(() => {
    fetchPreferences()
  }, [])

  const fetchPreferences = async () => {
    try {
      setLoading(true)
      const data = await studentAPI.getPreferences()
      setPreferences(data.preferences || [])
    } catch (err) {
      console.error('Failed to fetch preferences:', err)
    } finally {
      setLoading(false)
    }
  }

  const handleAdd = async (e) => {
    e.preventDefault()
    if (!value.trim()) return

    try {
      setAdding(true)
      setError('')
      await studentAPI.addPreference({
        preference_type: selectedType,
        preference_value: value.trim(),
      })
      setValue('')
      setSuccess('Preference added! You\'ll be notified about matching books.')
      setTimeout(() => setSuccess(''), 3000)
      fetchPreferences()
    } catch (err) {
      setError(err.message || 'Failed to add preference')
      setTimeout(() => setError(''), 4000)
    } finally {
      setAdding(false)
    }
  }

  const handleRemove = async (id) => {
    try {
      await studentAPI.removePreference(id)
      setPreferences(prev => prev.filter(p => p.id !== id))
      setSuccess('Preference removed.')
      setTimeout(() => setSuccess(''), 2000)
    } catch (err) {
      setError('Failed to remove preference')
      setTimeout(() => setError(''), 3000)
    }
  }

  const getTypeIcon = (type) => {
    switch (type) {
      case 'category': return '📂'
      case 'author': return '✍️'
      case 'title': return '📖'
      default: return '📌'
    }
  }

  const getTypeLabel = (type) => {
    switch (type) {
      case 'category': return 'Category'
      case 'author': return 'Author'
      case 'title': return 'Title'
      default: return type
    }
  }

  const selectedTypeInfo = PREFERENCE_TYPES.find(t => t.value === selectedType)

  if (loading) {
    return <div className="preferences-loading">Loading preferences...</div>
  }

  return (
    <div className="preferences-panel">
      <div className="preferences-header">
        <h2>📬 My Book Preferences</h2>
        <p className="preferences-subtitle">
          Tell us what you like — we'll notify you when matching books arrive!
        </p>
      </div>

      {error && (
        <div className="preferences-alert error">
          <span>❌ {error}</span>
        </div>
      )}

      {success && (
        <div className="preferences-alert success">
          <span>✅ {success}</span>
        </div>
      )}

      {/* Add Preference Form */}
      <form onSubmit={handleAdd} className="preference-form">
        <div className="preference-form-row">
          <div className="preference-type-selector">
            {PREFERENCE_TYPES.map(type => (
              <button
                key={type.value}
                type="button"
                className={`preference-type-btn ${selectedType === type.value ? 'active' : ''}`}
                onClick={() => setSelectedType(type.value)}
              >
                {type.label}
              </button>
            ))}
          </div>
          <div className="preference-input-group">
            <input
              type="text"
              value={value}
              onChange={(e) => setValue(e.target.value)}
              placeholder={selectedTypeInfo?.placeholder || 'Enter preference...'}
              className="preference-input"
              maxLength={255}
              id="preference-value-input"
            />
            <button
              type="submit"
              className="preference-add-btn"
              disabled={adding || !value.trim()}
            >
              {adding ? '...' : '+ Add'}
            </button>
          </div>
        </div>
      </form>

      {/* Preferences List */}
      <div className="preferences-list">
        {preferences.length === 0 ? (
          <div className="preferences-empty">
            <div className="preferences-empty-icon">🎯</div>
            <h3>No preferences set yet</h3>
            <p>Add your favorite genres, authors, or book titles above.</p>
            <p className="preferences-empty-hint">
              When a matching book is added to the library, you'll receive a notification instantly!
            </p>
          </div>
        ) : (
          <>
            <h3 className="preferences-list-title">
              Your Preferences ({preferences.length}/20)
            </h3>
            <div className="preference-chips">
              {preferences.map(pref => (
                <div key={pref.id} className={`preference-chip chip-${pref.preference_type}`}>
                  <span className="chip-icon">{getTypeIcon(pref.preference_type)}</span>
                  <span className="chip-label">{getTypeLabel(pref.preference_type)}</span>
                  <span className="chip-value">{pref.preference_value}</span>
                  <button
                    onClick={() => handleRemove(pref.id)}
                    className="chip-remove"
                    aria-label={`Remove ${pref.preference_value}`}
                    title="Remove preference"
                  >
                    ×
                  </button>
                </div>
              ))}
            </div>
          </>
        )}
      </div>

      {/* How It Works section */}
      <div className="preferences-info">
        <h4>🤖 How Notifications Work</h4>
        <div className="info-cards">
          <div className="info-card">
            <span className="info-step">1</span>
            <p>Set your preferred categories, authors, or titles</p>
          </div>
          <div className="info-card">
            <span className="info-step">2</span>
            <p>When a matching book is added or becomes available</p>
          </div>
          <div className="info-card">
            <span className="info-step">3</span>
            <p>You get an instant notification via the bell icon!</p>
          </div>
        </div>
      </div>
    </div>
  )
}

export default PreferencesPanel
