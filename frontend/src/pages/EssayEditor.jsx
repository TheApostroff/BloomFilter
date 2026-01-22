import { useState, useEffect, useRef } from 'react'
import RichTextarea from '../components/RichTextarea'

import apiFetch from '../utils/api'
import './EssayEditor.css'

function EssayEditor({ token, onNavigate }) {
  const existing = localStorage.getItem('editingEssay')
  const parsed = existing ? JSON.parse(existing) : null

  const [title, setTitle] = useState(parsed?.title || '')
  const [content, setContent] = useState(parsed?.content || '')
  const [fontSize, setFontSize] = useState(parsed?.font_size || 14)
  const [fontStyle, setFontStyle] = useState(parsed?.font_style || 'Arial')

  const [error, setError] = useState('')
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
      resp = await apiFetch(`/api/essays/`, { method: 'POST', body: JSON.stringify({ title, content, font_size: fontSize, font_style: fontStyle }) })

      console.log(resp.body)
      onNavigate('essays')
    } catch (err) {
      setError(err.message || 'Save failed')
    } finally {
      setLoading(false)
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
        <RichTextarea value={content} onChange={setContent} fontStyle={fontStyle} fontSize={fontSize} invalidWords={checks.filter(c => !c.valid)} />
      </div>
    </div>
  )
}

export default EssayEditor
