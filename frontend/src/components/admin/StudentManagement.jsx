import { useState, useEffect } from 'react'
import { adminAPI } from '../../utils/api'
import './StudentManagement.css'

const StudentManagement = () => {
  const [students, setStudents] = useState([])
  const [showForm, setShowForm] = useState(false)
  const [editingStudent, setEditingStudent] = useState(null)
  const [searchQuery, setSearchQuery] = useState('')
  const [loading, setLoading] = useState(false)
  const [formData, setFormData] = useState({
    username: '',
    password: '',
    name: '',
    email: '',
    phone: ''
  })
  const [errors, setErrors] = useState({})

  useEffect(() => {
    loadStudents()
  }, [])

  const loadStudents = async () => {
    try {
      const data = await adminAPI.getStudents()
      setStudents(data)
    } catch (err) {
      alert('Failed to load students')
    }
  }

  const handleSearch = async (query) => {
    setSearchQuery(query)
    try {
      const data = await adminAPI.searchStudents(query)
      setStudents(data)
    } catch (err) {
      alert('Search failed')
    }
  }

  const validateForm = () => {
    const newErrors = {}
    
    if (!editingStudent && !formData.username.trim()) {
      newErrors.username = 'Username is required'
    }
    if (!editingStudent && !formData.password) {
      newErrors.password = 'Password is required'
    }
    if (!formData.name.trim()) {
      newErrors.name = 'Name is required'
    }
    if (!formData.email.trim()) {
      newErrors.email = 'Email is required'
    }
    if (formData.email && !/\S+@\S+\.\S+/.test(formData.email)) {
      newErrors.email = 'Invalid email format'
    }
    if (!formData.phone.trim()) {
      newErrors.phone = 'Phone is required'
    }
    
    setErrors(newErrors)
    return Object.keys(newErrors).length === 0
  }

  const handleSubmit = async () => {
    if (!validateForm()) return
    
    setLoading(true)
    try {
      if (editingStudent) {
        // ✅ FIX: Use numeric ID, not registration_no
        await adminAPI.updateStudent(editingStudent.id, formData)
        alert('Student updated successfully!')
      } else {
        await adminAPI.addStudent(formData)
        alert('Student added successfully!')
      }
      
      resetForm()
      loadStudents()
    } catch (err) {
      alert(err.message || 'Operation failed')
    } finally {
      setLoading(false)
    }
  }

  const handleEdit = (student) => {
    setEditingStudent(student)
    setFormData({
      username: student.username,
      password: '',
      name: student.name,
      email: student.email || '',
      phone: student.phone || ''
    })
    setShowForm(true)
  }

  const handleDelete = async (id, name) => {
    if (!window.confirm(`Delete student "${name}"? This cannot be undone.`)) return
    
    try {
      // Try normal delete first
      const result = await adminAPI.deleteStudent(id, false)
      alert(result.message || 'Student deleted successfully!')
      loadStudents()
    } catch (err) {
      const msg = err.message || 'Failed to delete student'
      
      // If student has unreturned books, offer force-delete with lost-book fine
      if (msg.includes('unreturned book') || msg.includes('lost-book fine')) {
        const forceConfirm = window.confirm(
          `⚠️ ${msg}\n\n` +
          `This "lost-book fine" is the FULL REPLACEMENT COST of each unreturned book ` +
          `(different from the ₹10/day late fine).\n\n` +
          `Do you want to proceed with force-delete and charge the lost-book fine?`
        )
        if (forceConfirm) {
          try {
            const result = await adminAPI.deleteStudent(id, true)
            alert(
              `✅ ${result.message}\n` +
              `Lost-book fine charged: ₹${result.lost_book_fine?.toFixed(2) || 0}\n` +
              `Books marked as lost: ${result.books_lost || 0}`
            )
            loadStudents()
          } catch (forceErr) {
            alert(forceErr.message || 'Force delete failed')
          }
        }
      } else {
        alert(msg)
      }
    }
  }

  const resetForm = () => {
    setFormData({
      username: '',
      password: '',
      name: '',
      email: '',
      phone: ''
    })
    setErrors({})
    setEditingStudent(null)
    setShowForm(false)
  }

  return (
    <div className="student-management">
      <div className="manager-header">
        <h2>👥 Student Management</h2>
        <div className="header-actions">
          <input
            type="text"
            placeholder="Search by name, email, username, or reg. number..."
            value={searchQuery}
            onChange={(e) => handleSearch(e.target.value)}
            className="search-input"
          />
          <button onClick={() => {
            resetForm()
            setShowForm(!showForm)
          }} className="btn btn-primary">
            {showForm ? '✕ Close' : '+ Add Student'}
          </button>
        </div>
      </div>

      {showForm && (
        <div className="form-container">
          <h3>{editingStudent ? 'Edit Student' : 'Add New Student'}</h3>
          
          <div className="form-row">
            <div className="form-group">
              <label>Username {editingStudent ? '' : '*'}</label>
              <input
                type="text"
                value={formData.username}
                onChange={(e) => setFormData({...formData, username: e.target.value})}
                disabled={editingStudent}
                placeholder="Enter username"
              />
              {errors.username && <span className="error">{errors.username}</span>}
            </div>
            
            <div className="form-group">
              <label>Password {editingStudent ? '(leave blank to keep current)' : '*'}</label>
              <input
                type="password"
                value={formData.password}
                onChange={(e) => setFormData({...formData, password: e.target.value})}
                placeholder="Enter password"
              />
              {errors.password && <span className="error">{errors.password}</span>}
            </div>
          </div>

          <div className="form-group">
            <label>Full Name *</label>
            <input
              type="text"
              value={formData.name}
              onChange={(e) => setFormData({...formData, name: e.target.value})}
              placeholder="Enter full name"
            />
            {errors.name && <span className="error">{errors.name}</span>}
          </div>

          <div className="form-row">
            <div className="form-group">
              <label>Email *</label>
              <input
                type="email"
                value={formData.email}
                onChange={(e) => setFormData({...formData, email: e.target.value})}
                placeholder="student@example.com"
              />
              {errors.email && <span className="error">{errors.email}</span>}
            </div>
            
            <div className="form-group">
              <label>Phone *</label>
              <input
                type="tel"
                value={formData.phone}
                onChange={(e) => setFormData({...formData, phone: e.target.value})}
                placeholder="1234567890"
              />
              {errors.phone && <span className="error">{errors.phone}</span>}
            </div>
          </div>

          <div className="form-actions">
            <button onClick={handleSubmit} disabled={loading} className="btn btn-success">
              {loading ? 'Saving...' : (editingStudent ? '✓ Update' : '✓ Add Student')}
            </button>
            <button onClick={resetForm} className="btn btn-secondary">Cancel</button>
          </div>
        </div>
      )}

      <div className="students-table">
        <table>
          <thead>
            <tr>
              <th>Registration No.</th>
              <th>Name</th>
              <th>Username</th>
              <th>Email</th>
              <th>Phone</th>
              <th>Borrowed</th>
              <th>Fine</th>
              <th>Actions</th>
            </tr>
          </thead>
          <tbody>
            {students.length === 0 ? (
              <tr>
                <td colSpan="8" style={{textAlign: 'center', padding: '20px'}}>
                  No students found. Add your first student!
                </td>
              </tr>
            ) : (
              students.map(student => (
                <tr key={student.id}>
                  <td><strong>{student.registration_no}</strong></td>
                  <td>{student.name}</td>
                  <td>{student.username}</td>
                  <td>{student.email || '-'}</td>
                  <td>{student.phone || '-'}</td>
                  <td>{student.borrowed_books}</td>
                  <td>₹{student.fine_amount.toFixed(2)}</td>
                  <td>
                    <button onClick={() => handleEdit(student)} className="btn btn-sm btn-secondary">
                      ✏️ Edit
                    </button>
                    <button onClick={() => handleDelete(student.id, student.name)} className="btn btn-sm btn-danger">
                      🗑️ Delete
                    </button>
                  </td>
                </tr>
              ))
            )}
          </tbody>
        </table>
      </div>
    </div>
  )
}

export default StudentManagement
