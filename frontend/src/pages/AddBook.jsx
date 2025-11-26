import { useState } from 'react'
import apiFetch from '../utils/api'
import './AddBook.css'

function AddBook({ token, onSuccess }) {
  const [file, setFile] = useState(null)
  const [title, setTitle] = useState('')
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')
  const [success, setSuccess] = useState('')

  const handleFileChange = (e) => {
    const selectedFile = e.target.files[0]
    if (selectedFile) {
      if (!selectedFile.name.toLowerCase().endsWith('.txt') && !selectedFile.name.toLowerCase().endsWith('.pdf') && !selectedFile.name.toLowerCase().endsWith('.docx')) {
        setError('Only .txt, .pdf or .docx files are allowed')
        setFile(null)
      } else {
        setFile(selectedFile)
        setError('')
        // Auto-fill title from filename if not set
        if (!title) {
          setTitle(selectedFile.name.replace('.txt', ''))
        }
      }
    }
  }

  const handleSubmit = async (e) => {
    e.preventDefault()
    if (!token) {
      setError('Please login to upload a book')
      return
    }
    // Verify token before uploading to avoid executing upload with an invalid session
    try {
      const verifyRes = await fetch(`${import.meta.env.VITE_BACKEND_URL || 'http://localhost:8000'}/api/auth/verify`, {
        headers: { 'Authorization': `Bearer ${token}` }
      })
      if (!verifyRes.ok) {
        setError('Session invalid. Please login again.')
        // Clear stored token and notify parent
        localStorage.removeItem('authToken')
        localStorage.removeItem('username')
        window.location.reload()
        return
      }
    } catch (err) {
      setError('Cannot verify session: ' + err.message)
      return
    }
    
    if (!file) {
      setError('Please select a file')
      return
    }

    if (!title.trim()) {
      setError('Please enter a book title')
      return
    }

    setLoading(true)
    setError('')
    setSuccess('')

    try {
      const formData = new FormData()
      formData.append('file', file)
      formData.append('title', title)
      // Do not append token to form data; apiFetch will add Authorization header when token is present in localStorage
      const response = await apiFetch('/api/books/upload', {
        method: 'POST',
        body: formData
      })

      // If apiFetch didn't throw, we have the parsed JSON payload in `response`
      setSuccess(response.message)
      if (response.duplicate) {
        setError(`Upload seems to be a duplicate (score ${Math.round(response.duplicate_score*100)}%). Consider skipping upload or force re-upload.`)
      }
      setFile(null)
      setTitle('')
      
      // Reset form and navigate back after 2 seconds
      setTimeout(() => {
        onSuccess()
      }, 2000)
    } catch (err) {
      const msg = err && err.message && err.message.includes('Failed to fetch')
        ? 'Server connection error: Cannot reach backend. Ensure backend is running and accessible.'
        : 'Server connection error: ' + err.message
      setError(msg)
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="add-book-page">
      <div className="add-book-container">
        <h2>Upload a Book</h2>
        <p className="subtitle">Upload a text file to index quotes using Bloom Filter</p>
        {!token && (
          <div className="warning">Please login to upload books. Go to Dashboard and click Login if you do not have an account.</div>
        )}

        <form onSubmit={handleSubmit} className="upload-form">
          <div className="form-group">
            <label htmlFor="title">Book Title</label>
            <input
              id="title"
              type="text"
              placeholder="Enter the book title"
              value={title}
              onChange={(e) => setTitle(e.target.value)}
              disabled={loading}
            />
          </div>

          <div className="form-group">
            <label htmlFor="file">Text File (.txt, .pdf, .docx)</label>
            <div className="file-input-wrapper">
              <input
                id="file"
                type="file"
                accept=".txt,.pdf,.docx"
                onChange={handleFileChange}
                disabled={loading || !token}
                className="file-input"
              />
              <label htmlFor="file" className="file-label">
                {file ? `Selected: ${file.name}` : 'Choose a file (.txt .pdf .docx)'}
              </label>
            </div>
          </div>

          {error && <div className="error-message">{error}</div>}
          {success && <div className="success-message">{success}</div>}

          <button
            type="submit"
            disabled={loading || !file || !token}
            className="upload-button"
          >
            {loading ? 'Uploading and Indexing...' : 'Upload Book'}
          </button>
        </form>

        <div className="info-box">
          <h4>About Bloom Filter</h4>
          <ul>
            <li>Fast membership testing with minimal space overhead</li>
            <li>No false negatives - if quote not found, it's definitely not in the set</li>
            <li>Possible false positives - if quote found, it might or might not be in the set</li>
            <li>Perfect for large-scale quote search engines</li>
          </ul>
        </div>
      </div>
    </div>
  )
}

export default AddBook
