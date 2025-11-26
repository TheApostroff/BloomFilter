import { useState, useEffect } from 'react'
import apiFetch from '../utils/api'
import './Dashboard.css'

function Dashboard({ token }) {
  const [books, setBooks] = useState([])
  const [stats, setStats] = useState(null)
  const [totalBooks, setTotalBooks] = useState(0)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')

  useEffect(() => {
    fetchData()
    // Refresh statistics every 5 seconds
    const interval = setInterval(fetchData, 5000)
    return () => clearInterval(interval)
  }, [token])

  const fetchData = async () => {
    if (!token) return
    try {
      const booksData = await apiFetch('/api/books')
      const statsData = await apiFetch('/api/bloom-filter/stats')
      setBooks(booksData.books || [])
      setStats(statsData.stats)
      setTotalBooks(statsData.total_books ?? totalBooks)

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
        <p>Welcome! Manage your books and search through quotes using Bloom Filter</p>
      </div>

      {error && <div className="error-message">{error}</div>}

      {/* Bloom Filter Statistics */}
      {stats && (
        <div className="stats-container">
          <h3>Bloom Filter Statistics</h3>
          <div className="stats-grid">
            <div className="stat-card">
              <div className="stat-label">Total Books</div>
              <div className="stat-value">{totalBooks}</div>
            </div>
            {/* <div className="stat-card">
              <div className="stat-label">Total Quotes</div>
              <div className="stat-value">{stats.total_quotes}</div>
            </div>
            <div className="stat-card">
              <div className="stat-label">Filter Size</div>
              <div className="stat-value">{stats.size}</div>
            </div>
            <div className="stat-card">
              <div className="stat-label">Bits Set</div>
              <div className="stat-value">{stats.bits_set}</div>
            </div>
            <div className="stat-card">
              <div className="stat-label">Fill %</div>
              <div className="stat-value">{stats.fill_percentage.toFixed(2)}%</div>
            </div>
            <div className="stat-card">
              <div className="stat-label">Hash Functions</div>
              <div className="stat-value">{stats.num_hashes}</div>
            </div> */}
          </div>
        </div>
      )}

      {/* Books List */}
      <div className="books-section">
        <h3>Uploaded Books</h3>
        {loading ? (
          <p>Loading books...</p>
        ) : books.length === 0 ? (
          <div className="empty-state">
            <p>No books uploaded yet. Start by uploading a book!</p>
          </div>
        ) : (
          <div className="books-list">
            {books.map((book) => (
              <div key={book.id} className="book-card">
                <div className="book-info">
                  <h4>{book.title}</h4>
                  <p className="book-meta">
                    Uploaded: {new Date(book.upload_date).toLocaleDateString()}
                  </p>
                  <p className="book-meta">
                    Quotes indexed: {book.quotes_count}
                  </p>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>

      {/* Quick Info */}
      <div className="info-section">
        <h3>How to use?</h3>
        <div className="info-grid">
          <div className="info-card">
            <h4>📚 Add Books</h4>
            <p>Upload text files (.txt) to index quotes using Bloom Filter</p>
          </div>
          <div className="info-card">
            <h4>🔍 Search Quotes</h4>
            <p>Use the search feature to find quotes and their sources</p>
          </div>
          <div className="info-card">
            <h4>⚡ Bloom Filter</h4>
            <p>Efficient data structure for quick membership testing</p>
          </div>
        </div>
      </div>
    </div>
  )
}

export default Dashboard
