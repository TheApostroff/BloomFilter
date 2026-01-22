import { useState, useEffect } from 'react'
import apiFetch from '../utils/api'
import './Essays.css'

function Essays({ token, onNavigate }) {
  const [essays, setEssays] = useState([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')

  useEffect(() => {
    fetchEssays()
  }, [token])

  const fetchEssays = async () => {
    setLoading(true)
    try {
      const res = await apiFetch('/api/essays')
      setEssays(res.essays || [])
      setError('')
    } catch (err) {
      setError(err.message || 'Failed to load essays')
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="essays-page">
      <div className="essays-container">
        <h2>Your Essays</h2>
        <div className="essays-actions">
          <button onClick={() => {onNavigate('essay-editor'); localStorage.removeItem('editingEssay');}}>Create New Essay</button>
        </div>
        {loading && <p>Loading...</p>}
        {error && <div className="error-message">{error}</div>}
        {!loading && essays.length === 0 && (
          <div>No essays yet. Click 'Create New Essay' to start writing.</div>
        )}
        <div className="essays-list">
          {essays.map(e => (
            <div className="essay-card" key={e.id}>
              <h4>{e.title}</h4>
              <div className="meta">
                <em>Updated: {new Date(e.updated_at).toLocaleString()}</em>
              </div>
              <div className="actions">
                <button onClick={() => {localStorage.setItem('editingEssay', JSON.stringify(e)); onNavigate('essay-editor')}}>Edit</button>
              </div>
            </div>
          ))}
        </div>
      </div>
    </div>
  )
}

export default Essays
