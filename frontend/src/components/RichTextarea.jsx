import { useState, useRef, useEffect } from 'react'
import './RichTextarea.css'

function RichTextarea({ value, onChange, fontSize, fontStyle, invalidWords = [] }) {
  const textareaRef = useRef(null)
  const highlightRef = useRef(null)

  useEffect(() => {
    if (highlightRef.current && value) {
      let highlightedHTML = value

      // Highlight invalid words
      if (invalidWords.length > 0) {
        invalidWords.forEach(word => {
          const regex = new RegExp(`\\b(${word.value})\\b`, 'gi')
          highlightedHTML = highlightedHTML.replace(
            regex,
            '<mark class="invalid-word">'+word.value +'</mark>'
          )
        })
      }

      highlightRef.current.innerHTML = highlightedHTML
    }
  }, [value, invalidWords])

  const handleScroll = () => {
    if (highlightRef.current && textareaRef.current) {
      highlightRef.current.scrollTop = textareaRef.current.scrollTop
      highlightRef.current.scrollLeft = textareaRef.current.scrollLeft
    }
  }

  return (
    <div className="rich-textarea-container">
      <div className="textarea-wrapper">
        <pre className="highlight-layer" style={{ fontSize: fontSize + 'px', fontFamily: fontStyle }} ref={highlightRef}><code></code></pre>
        <textarea
          ref={textareaRef}
          value={value}
          onChange={(e) => onChange(e.target.value)}
          onScroll={handleScroll}
          className="textarea-input"
          style={{ fontSize: fontSize + 'px', fontFamily: fontStyle }}
          placeholder="Start typing..."
          spellCheck="false"
        />
      </div>
    </div>
  )
}

export default RichTextarea