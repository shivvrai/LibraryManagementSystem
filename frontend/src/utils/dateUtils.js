export function formatDate(dateString) {
  if (!dateString) return 'N/A'
  const date = new Date(dateString)
  return date.toLocaleDateString('en-IN', {
    year: 'numeric',
    month: 'short',
    day: 'numeric'
  })
}

export function calculateDaysRemaining(dueDate) {
  if (!dueDate) return 0
  const due = new Date(dueDate)
  const today = new Date()
  const diff = due - today
  return Math.ceil(diff / (1000 * 60 * 60 * 24))
}

export function isOverdue(dueDate) {
  return calculateDaysRemaining(dueDate) < 0
}

export function getDueDateStatus(daysRemaining) {
  if (daysRemaining < 0) return 'overdue'
  if (daysRemaining <= 2) return 'due-soon'
  return 'ok'
}

export function calculateFine(dueDate, finePerDay = 10) {
  const daysOverdue = Math.abs(Math.min(0, calculateDaysRemaining(dueDate)))
  return daysOverdue * finePerDay
}

export function getReturnDate(borrowDate, days = 7) {
  const borrow = new Date(borrowDate)
  const returnDate = new Date(borrow)
  returnDate.setDate(returnDate.getDate() + days)
  return returnDate.toISOString()
}
