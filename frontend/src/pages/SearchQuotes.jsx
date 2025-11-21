import { useState } from 'react'
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
      const response = await fetch(`http://localhost:8000/api/quotes/search?token=${token}`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          quote: quote
        })
      })

      const data = await response.json()

      if (!response.ok) {
        setError(data.detail || 'Search failed')
        return
      }

      setResult(data)
    } catch (err) {
      setError('Server connection error: ' + err.message)
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

    setLoading(true)
    setError('')

    try {
      const response = await fetch(`http://localhost:8000/api/quotes/add?token=${token}`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          quote: quote,
          book_title: bookTitle
        })
      })

      const data = await response.json()

      if (!response.ok) {
        setError(data.detail || 'Add failed')
        return
      }

      setResult({
        found: true,
        message: data.message,
        sources: [bookTitle]
      })
    } catch (err) {
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
              disabled={loading}
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
            <div className="result-content">
              <p><strong>Message:</strong> {result.message}</p>
              
              {result.sources && result.sources.length > 0 && (
                <div className="sources">
                  <strong>Sources:</strong>
                  <ul>
                    {result.sources.map((source, idx) => (
                      <li key={idx}>{source}</li>
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

