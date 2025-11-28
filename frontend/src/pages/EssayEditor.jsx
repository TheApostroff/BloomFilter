import { useState, useEffect, useRef } from 'react'
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
  // const [books, setBooks] = useState([])
  // const [selectedBook, setSelectedBook] = useState(null)
  // const [bookQuotes, setBookQuotes] = useState([])

  // useEffect(() => {
  //   // fetch books for quotes selection
  //   fetchBooks()
  // }, [])

  // const fetchBooks = async () => {
  //   try {
  //     const data = await apiFetch('/api/books')
  //     setBooks(data.books || [])
  //   } catch (err) {
  //     // ignore
  //   }
  // }

  // const loadQuotes = async (book) => {
  //   if (!book) return
  //   try {
  //     const res = await apiFetch(`/api/books/${book.id}/quotes`)
  //     setBookQuotes(res.quotes || [])
  //     setSelectedBook(book)
  //   } catch (err) {
  //     setBookQuotes([])
  //   }
  // }

  // const handleInsertQuote = (quote) => {
  //   setContent(prev => prev + '\n"' + quote + '"')
  // }

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
        <div className="editor-main">
          <textarea style={{ fontSize: fontSize + 'px', fontFamily: fontStyle }} value={content} onChange={(e) => setContent(e.target.value)}></textarea>
          <div className="spellcheck-panel">
            <div className="spellcheck-summary">
              <strong>Words checked:</strong> {checks.length}
              {checks.length > 0 && (
                <>
                  {' '}| <strong>Invalid:</strong> {checks.filter(c => !c.valid).length}
                </>
              )}
            </div>
            {checks.length > 0 && (
              <div className="spellcheck-list">
                {checks.slice(0, 50).map((c, idx) => (
                  <div key={idx} className={`spellcheck-item ${c.valid ? 'ok' : 'bad'}`}>
                    { !c.valid && <span className="val">{c.value} invalid</span>}
                  </div>
                ))}
                {checks.length > 50 && (
                  <div className="spellcheck-more">…and {checks.length - 50} more</div>
                )}
              </div>
            )}
          </div>
          {/* <div className="quote-helper"> */}
            {/* <h4>Insert Quote</h4> */}
            {/* <div> */}
              {/* <select onChange={(e) => { const id = parseInt(e.target.value); const book = books.find(b=>b.id===id); loadQuotes(book) }}>
                <option value="">Select a book</option>
                {books.map(b => <option key={b.id} value={b.id}>{b.title}</option>)}
              </select> */}
            {/* </div> */}
            {/* <div className="quote-list"> */}
              {/* {bookQuotes.map((q, idx) => <div key={idx} className="q-item" onClick={()=>handleInsertQuote(q)}>{q}</div>)} */}
            {/* </div> */}
          {/* </div> */}
        </div>
        {error && <div className="error-message">{error}</div>}
      </div>
    </div>
  )
}

export default EssayEditor
