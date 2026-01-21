import { useState, useEffect, useRef } from 'react'
import RichTextarea from '../components/RichTextarea'

import apiFetch from '../utils/api'
import './EssayEditor.css'

function EssayEditor({ token, onNavigate }) {

  const [title, setTitle] = useState('')
  const [content, setContent] = useState('')
  const [fontSize, setFontSize] = useState(14)
  const [fontStyle, setFontStyle] = useState('Arial')
  const [loading, setLoading] = useState(false)
  const [checks, setChecks] = useState([])
  const debounceRef = useRef(null)

  // Debounced spellcheck when content changes
  useEffect(() => {
    // clear pending timer
    if (debounceRef.current) clearTimeout(debounceRef.current)

    // quick exit for empty content
    if (!content || !content.trim()) {
      setChecks([])
      return
    }

    debounceRef.current = setTimeout(async () => {
      try {
        // Extract words locally to keep payload compact (unique words)
        const words = Array.from(new Set((content.match(/[^\s]+/g) || [])))
        const res = await apiFetch('/api/spellcheck', {
          method: 'POST',
          body: JSON.stringify({ words }),
        })
        setChecks(Array.isArray(res?.results) ? res.results : [])
      } catch (e) {
        // Non-fatal; don't block editor
      }
    }, 400)

    return () => {
      if (debounceRef.current) clearTimeout(debounceRef.current)
    }
  }, [content])

  const handleSave = async () => {
    if (!token) { setError('Please login to save'); return }
    setLoading(true)
    setError('')
    try {
      let resp
      if (parsed) {
        resp = await apiFetch(`/api/essays/${parsed.id}`, { method: 'PUT', body: JSON.stringify({ title, content, font_size: fontSize, font_style: fontStyle }) })
      } else {
        resp = await apiFetch('/api/essays', { method: 'POST', body: JSON.stringify({ title, content, font_size: fontSize, font_style: fontStyle }) })
      }
      onNavigate('essays')
    } catch (err) {
      setError(err.message || 'Save failed')
    } finally {
      setLoading(false)
      localStorage.removeItem('editingEssay')
    }
  }

  return (
    <div className="essay-editor-page">
      <div className="editor-container">
        <div className="toolbar">
          <input placeholder="Essay Title" value={title} onChange={(e) => setTitle(e.target.value)} />
          <select value={fontStyle} onChange={(e) => setFontStyle(e.target.value)}>
            <option>Arial</option>
            <option>Times New Roman</option>
            <option>Courier New</option>
          </select>
          <input type="number" value={fontSize} onChange={(e) => setFontSize(parseInt(e.target.value))} min={8} max={72} />
          <button onClick={() => onNavigate('essays')}>Back</button>
          <button onClick={handleSave} disabled={loading}>{loading ? 'Saving...' : 'Save'}</button>
        </div>
          <RichTextarea value={content} onChange={setContent} invalidWords={checks.filter(c => !c.valid)}/>
      </div>
    </div>
  )
}

export default EssayEditor
