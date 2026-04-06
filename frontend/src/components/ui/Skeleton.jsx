const Skeleton = ({ variant = 'text', width, height, count = 1, className = '' }) => {
  const items = Array.from({ length: count })

  const getStyle = () => {
    const base = {}
    if (width) base.width = width
    if (height) base.height = height
    return base
  }

  return items.map((_, i) => (
    <div
      key={i}
      className={`skeleton skeleton--${variant} ${className}`}
      style={getStyle()}
      aria-hidden="true"
    />
  ))
}

export const BookCardSkeleton = () => (
  <div className="book-card book-card--skeleton">
    <div className="skeleton skeleton--rect" style={{ height: '140px', borderRadius: '8px 8px 0 0' }} />
    <div style={{ padding: '16px' }}>
      <div className="skeleton skeleton--text" style={{ width: '80%', marginBottom: '8px' }} />
      <div className="skeleton skeleton--text" style={{ width: '50%', marginBottom: '16px' }} />
      <div className="skeleton skeleton--text" style={{ width: '60%', marginBottom: '8px' }} />
      <div className="skeleton skeleton--text" style={{ width: '40%' }} />
    </div>
  </div>
)

export const TableRowSkeleton = ({ cols = 5 }) => (
  <tr className="skeleton-row">
    {Array.from({ length: cols }).map((_, i) => (
      <td key={i}>
        <div className="skeleton skeleton--text" style={{ width: `${60 + Math.random() * 30}%` }} />
      </td>
    ))}
  </tr>
)

export default Skeleton
