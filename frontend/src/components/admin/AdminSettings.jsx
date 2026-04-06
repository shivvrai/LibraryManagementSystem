import { useState, useEffect } from 'react'
import { adminAPI } from '../../utils/api'

const AdminSettings = () => {
  const [profile, setProfile] = useState(null)
  const [loading, setLoading] = useState(true)
  const [activeSection, setActiveSection] = useState('profile')

  // Profile edit
  const [profileForm, setProfileForm] = useState({ name: '' })
  const [profileSaving, setProfileSaving] = useState(false)
  const [profileMsg, setProfileMsg] = useState(null)

  // Password change
  const [pwdForm, setPwdForm] = useState({ old_password: '', new_password: '', confirm: '' })
  const [pwdSaving, setPwdSaving] = useState(false)
  const [pwdMsg, setPwdMsg] = useState(null)

  useEffect(() => {
    loadProfile()
  }, [])

  const loadProfile = async () => {
    try {
      setLoading(true)
      const data = await adminAPI.getProfile()
      setProfile(data)
      setProfileForm({ name: data.name || '' })
    } catch (e) {
      console.error('Failed to load admin profile:', e)
    } finally {
      setLoading(false)
    }
  }

  const handleProfileSave = async (e) => {
    e.preventDefault()
    setProfileSaving(true)
    setProfileMsg(null)
    try {
      const res = await adminAPI.updateProfile({ name: profileForm.name.trim() })
      setProfile(prev => ({ ...prev, name: res.name }))
      setProfileMsg({ type: 'success', text: '✓ Profile updated successfully!' })
    } catch (e) {
      setProfileMsg({ type: 'error', text: e.message || 'Failed to update profile' })
    } finally {
      setProfileSaving(false)
    }
  }

  const handlePasswordSave = async (e) => {
    e.preventDefault()
    setPwdMsg(null)
    if (pwdForm.new_password !== pwdForm.confirm) {
      setPwdMsg({ type: 'error', text: 'New passwords do not match' })
      return
    }
    if (pwdForm.new_password.length < 6) {
      setPwdMsg({ type: 'error', text: 'New password must be at least 6 characters' })
      return
    }
    setPwdSaving(true)
    try {
      await adminAPI.updateProfile({
        old_password: pwdForm.old_password,
        new_password: pwdForm.new_password,
      })
      setPwdMsg({ type: 'success', text: '✓ Password changed successfully!' })
      setPwdForm({ old_password: '', new_password: '', confirm: '' })
    } catch (e) {
      setPwdMsg({ type: 'error', text: e.message || 'Failed to change password' })
    } finally {
      setPwdSaving(false)
    }
  }

  if (loading) {
    return (
      <div className="settings-loading">
        <div className="spinner" />
      </div>
    )
  }

  const formatDate = (dt) => dt ? new Date(dt).toLocaleDateString('en-IN', { year: 'numeric', month: 'long', day: 'numeric' }) : '—'

  return (
    <div className="settings-page animate-fadeInUp">
      <div className="settings-header">
        <h2 className="settings-title">⚙️ Admin Settings</h2>
        <p className="settings-subtitle">Manage your administrator account</p>
      </div>

      <div className="settings-layout">
        <nav className="settings-nav">
          {[
            { id: 'profile', icon: '👤', label: 'Profile' },
            { id: 'password', icon: '🔒', label: 'Password' },
            { id: 'account', icon: 'ℹ️', label: 'Account Info' },
          ].map(s => (
            <button
              key={s.id}
              className={`settings-nav-btn ${activeSection === s.id ? 'active' : ''}`}
              onClick={() => setActiveSection(s.id)}
            >
              <span>{s.icon}</span>
              <span>{s.label}</span>
            </button>
          ))}
        </nav>

        <div className="settings-content">

          {/* ── Profile ── */}
          {activeSection === 'profile' && (
            <div className="settings-panel">
              <h3 className="settings-panel-title">Edit Profile</h3>
              <p className="settings-panel-desc">Update your administrator display name.</p>
              <form onSubmit={handleProfileSave} className="settings-form">
                <div className="settings-form-group">
                  <label>Full Name</label>
                  <input
                    type="text"
                    value={profileForm.name}
                    onChange={e => setProfileForm({ name: e.target.value })}
                    placeholder="Administrator name"
                    required
                  />
                </div>
                {profileMsg && (
                  <div className={`settings-msg ${profileMsg.type}`}>{profileMsg.text}</div>
                )}
                <button type="submit" className="btn btn--primary" disabled={profileSaving}>
                  {profileSaving ? 'Saving...' : 'Save Changes'}
                </button>
              </form>
            </div>
          )}

          {/* ── Password ── */}
          {activeSection === 'password' && (
            <div className="settings-panel">
              <h3 className="settings-panel-title">Change Password</h3>
              <p className="settings-panel-desc">Choose a strong password with at least 6 characters.</p>
              <form onSubmit={handlePasswordSave} className="settings-form">
                <div className="settings-form-group">
                  <label>Current Password</label>
                  <input
                    type="password"
                    value={pwdForm.old_password}
                    onChange={e => setPwdForm(p => ({ ...p, old_password: e.target.value }))}
                    placeholder="Enter current password"
                    required
                  />
                </div>
                <div className="settings-form-group">
                  <label>New Password</label>
                  <input
                    type="password"
                    value={pwdForm.new_password}
                    onChange={e => setPwdForm(p => ({ ...p, new_password: e.target.value }))}
                    placeholder="At least 6 characters"
                    required
                  />
                </div>
                <div className="settings-form-group">
                  <label>Confirm New Password</label>
                  <input
                    type="password"
                    value={pwdForm.confirm}
                    onChange={e => setPwdForm(p => ({ ...p, confirm: e.target.value }))}
                    placeholder="Re-enter new password"
                    required
                  />
                </div>
                {pwdMsg && (
                  <div className={`settings-msg ${pwdMsg.type}`}>{pwdMsg.text}</div>
                )}
                <button type="submit" className="btn btn--primary" disabled={pwdSaving}>
                  {pwdSaving ? 'Changing...' : 'Change Password'}
                </button>
              </form>
            </div>
          )}

          {/* ── Account Info ── */}
          {activeSection === 'account' && (
            <div className="settings-panel">
              <h3 className="settings-panel-title">Account Information</h3>
              <p className="settings-panel-desc">Read-only details about your administrator account.</p>
              <div className="settings-info-grid">
                <div className="settings-info-item">
                  <span className="settings-info-label">Username</span>
                  <span className="settings-info-value">@{profile?.username}</span>
                </div>
                <div className="settings-info-item">
                  <span className="settings-info-label">Role</span>
                  <span className="settings-info-value settings-badge settings-badge--admin">{profile?.role || 'admin'}</span>
                </div>
                <div className="settings-info-item">
                  <span className="settings-info-label">Member Since</span>
                  <span className="settings-info-value">{formatDate(profile?.created_at)}</span>
                </div>
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  )
}

export default AdminSettings
