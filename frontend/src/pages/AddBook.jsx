import { useState } from 'react'
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
      if (!selectedFile.name.endsWith('.txt')) {
        setError('Only .txt files are allowed')
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
      formData.append('token', token)

      const response = await fetch('http://localhost:8000/api/books/upload', {
        method: 'POST',
        body: formData
      })

      const data = await response.json()

      if (!response.ok) {
        setError(data.detail || 'Upload failed')
        return
      }

      setSuccess(data.message)
      setFile(null)
      setTitle('')
      
      // Reset form and navigate back after 2 seconds
      setTimeout(() => {
        onSuccess()
      }, 2000)
    } catch (err) {
      setError('Server connection error: ' + err.message)
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="add-book-page">
      <div className="add-book-container">
        <h2>Upload a Book</h2>
        <p className="subtitle">Upload a text file to index quotes using Bloom Filter</p>

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
            <label htmlFor="file">Text File (.txt)</label>
            <div className="file-input-wrapper">
              <input
                id="file"
                type="file"
                accept=".txt"
                onChange={handleFileChange}
                disabled={loading}
                className="file-input"
              />
              <label htmlFor="file" className="file-label">
                {file ? `Selected: ${file.name}` : 'Choose a text file'}
              </label>
            </div>
          </div>

          {error && <div className="error-message">{error}</div>}
          {success && <div className="success-message">{success}</div>}

          <button
            type="submit"
            disabled={loading || !file}
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
