import { useState, useEffect } from 'react'
import apiFetch from '../utils/api'
import './Dashboard.css'

function Dashboard({ token }) {
  const [stats, setStats] = useState(null)
  const [essays, setEssays] = useState([])
  const [totalEssays, setTotalEssays] = useState(0)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')

  useEffect(() => {
    fetchData()
    // Refresh statistics every 5 seconds
    const interval = setInterval(fetchData, 5*1000)
    return () => clearInterval(interval)
  }, [token])

  const fetchData = async () => {
    if (!token) return
    try {
      // const booksData = await apiFetch('/api/books')
      const statsData = await apiFetch('/api/bloom-filter/stats')
      const essaysData = await apiFetch('/api/essays')
      
      // setBooks(booksData.books || [])
      setStats(statsData.stats)
      setEssays(essaysData.essays || [])
      setTotalEssays(essaysData.essays?.length || 0)
      // setTotalBooks(statsData.total_books ?? totalBooks)

      setError('')
    } catch (err) {
      // Differentiate network errors (backend not running) from server errors
      const msg = err && err.message && err.message.includes('Failed to fetch')
        ? 'Error loading data: Cannot reach backend. Ensure backend is running (http://localhost:8000) and CORS is configured.'
        : 'Error loading data: ' + err.message
      setError(msg)
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="dashboard">
      <div className="dashboard-header">
        <h2>Dashboard</h2>
        {/* <p>Welcome! Manage your books and search through quotes using Bloom Filter</p> */}
      </div>

      {error && <div className="error-message">{error}</div>}

      {/* Bloom Filter Statistics */}
      {stats && (
        <div className="stats-container">
          <h3>Bloom Filter Statistics</h3>
          <div className="stats-grid">
            <div className="stat-card">
              <div className="stat-label">Total Essays</div>
              <div className="stat-value">{totalEssays}</div>
            </div>
            <div className="stat-card">
              <div className="stat-label">Max Filter Size</div>
              <div className="stat-value">{stats.max_size}</div>
            </div>
            <div className="stat-card">
              <div className="stat-label">Current Filter Size</div>
              <div className="stat-value">{stats.current_size}</div>
            </div>
            <div className="stat-card">
              <div className="stat-label">Filter current size</div>
              <div className="stat-value">{((100 / stats.max_size) * stats.current_size).toFixed(4)}%</div>
            </div>
            <div className="stat-card">
              <div className="stat-label">Hash count</div>
              <div className="stat-value">{stats.hash_count}</div>
            </div>
          </div>
        </div>
      )}

      {/* Essays List */}
      <div className="books-section">
        <h3>My Essays</h3>
        {loading ? (
          <p>Loading essays...</p>
        ) : essays.length === 0 ? (
          <div className="empty-state">
            <p>No essays yet. Start by creating your first essay!</p>
          </div>
        ) : (
          <div className="books-list">
            {essays.map((essay) => (
              <div key={essay.id} className="book-card">
                <div className="book-info">
                  <h4>{essay.title}</h4>
                  <p className="book-meta">
                    Created: {new Date(essay.created_at).toLocaleDateString()}
                  </p>
                  <p className="book-meta">
                    Updated: {new Date(essay.updated_at).toLocaleDateString()}
                  </p>
                  <p className="book-meta">
                    Font: {essay.font_style} • Size: {essay.font_size}px
                  </p>
                  <p className="essay-preview" style={{fontSize: essay.font_size + 'px', fontFamily: essay.font_style }}>
                    {essay.content.substring(0, 10)}
                    {essay.content.length > 150 ? '...' : ''}
                  </p>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  )
}

export default Dashboard
