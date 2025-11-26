import { useState } from 'react'
import apiFetch from '../utils/api'
import './SearchQuotes.css'

function SearchQuotes({ token }) {
  const [quote, setQuote] = useState('')
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')
  const [result, setResult] = useState(null)
  const [searched, setSearched] = useState(false)

  const handleSearch = async (e) => {
    e.preventDefault()

    if (!quote.trim()) {
      setError('Please enter a quote to search')
      return
    }

    setLoading(true)
    setError('')
    setResult(null)
    setSearched(true)

    try {
      const payload = await apiFetch('/api/quotes/search', {
        method: 'POST',
        body: JSON.stringify({ quote: quote })
      })
      setResult(payload)
    } catch (err) {
      const msg = err && err.message && err.message.includes('Failed to fetch')
        ? 'Server connection error: Cannot reach backend. Ensure backend is running and accessible.'
        : 'Server connection error: ' + err.message
      setError(msg)
    } finally {
      setLoading(false)
    }
  }

  const handleAddQuote = async (e) => {
    e.preventDefault()
    
    if (!quote.trim()) {
      setError('Please enter a quote')
      return
    }

    const bookTitle = prompt('Enter the book title for this quote:')
    if (!bookTitle) return

    // verify token before calling protected endpoint
    if (!token) {
      setError('Please login to add a quote')
      return
    }
    try {
      const verifyRes = await fetch(`${import.meta.env.VITE_BACKEND_URL || 'http://localhost:8000'}/api/auth/verify`, { headers: { 'Authorization': `Bearer ${token}` } })
      if (!verifyRes.ok) {
        setError('Session invalid. Please login again.')
        localStorage.removeItem('authToken')
        localStorage.removeItem('username')
        window.location.reload()
        return
      }
    } catch (err) {
      setError('Cannot verify session: ' + err.message)
      return
    }

    setLoading(true)
    setError('')

    try {
      const payload = await apiFetch('/api/quotes/add', {
        method: 'POST',
        body: JSON.stringify({ quote: quote, book_title: bookTitle })
      })
      setResult({ found: true, message: payload.message, sources: [bookTitle] })
    } catch (err) {
      if (err && err.status === 409) {
        setError('Quote already exists. No need to add it again.')
        return
      }
      setError('Server connection error: ' + err.message)
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="search-page">
      <div className="search-container">
        <h2>Search Quotes</h2>
        <p className="subtitle">Search for quotes in your indexed books using Bloom Filter</p>

        <form onSubmit={handleSearch} className="search-form">
          <div className="form-group">
            <label htmlFor="quote">Quote Text</label>
            <textarea
              id="quote"
              placeholder="Enter the quote you want to search..."
              value={quote}
              onChange={(e) => setQuote(e.target.value)}
              disabled={loading}
              rows="4"
              className="quote-textarea"
            />
          </div>

          {error && <div className="error-message">{error}</div>}

          <div className="button-group">
            <button
              type="submit"
              disabled={loading}
              className="search-button"
            >
              {loading ? 'Searching...' : '🔍 Search Quote'}
            </button>

            <button
              type="button"
              onClick={handleAddQuote}
              disabled={loading || !token}
              className="add-button"
            >
              {loading ? 'Adding...' : '➕ Add Quote'}
            </button>
          </div>
        </form>

        {/* Search Results */}
        {searched && result && (
          <div className={`result-container ${result.found ? 'found' : 'not-found'}`}>
            <div className="result-header">
              {result.found ? '✅ Quote Found' : '❌ Quote Not Found'}
            </div>
            {result.found && result.sources && (
              <div className="result-meta">
                <strong>Occurrences:</strong> {result.sources.length}
                <span style={{marginLeft:12}}><strong>Books:</strong> {Array.from(new Set(result.sources.map(s => s.title))).length}</span>
              </div>
            )}
            <div className="result-content">
              <p><strong>Message:</strong> {result.message}</p>
              
              {result.sources && result.sources.length > 0 && (
                <div className="sources">
                  <strong>Sources:</strong>
                  <ul>
                    {result.sources.map((source, idx) => (
                      <li key={idx}>
                        <div className="source-title">{source.title}</div>
                        {source.page && <div>📄 Page: {source.page}</div>}
                        {source.paragraph && <div>¶ Paragraph: {source.paragraph}</div>}
                        {source.row && <div>— Row: {source.row}</div>}
                        {source.snippet && <div className="snippet">"{source.snippet}"</div>}
                      </li>
                    ))}
                  </ul>
                </div>
              )}
            </div>
          </div>
        )}

        {/* Bloom Filter Explanation */}
          <div className="info-box">
          <h3>How Bloom Filter Search Works</h3>
          <div className="explanation">
            <div className="explanation-item">
              <h4>✅ Quote Found</h4>
              <p>The quote is possibly in the database. Check the sources to verify.</p>
              <p><small>Note: Bloom Filter can have false positives</small></p>
            </div>
            <div className="explanation-item">
              <h4>❌ Quote Not Found</h4>
              <p>The quote is definitely NOT in the database.</p>
              <p><small>Note: Bloom Filter has NO false negatives</small></p>
            </div>
          </div>
        </div>
      </div>
    </div>
  )
}

export default SearchQuotes

