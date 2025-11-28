import { useState } from 'react'
import './SignupPage.css'
import apiFetch from '../utils/api'

function SignupPage({ onLogin, onCancel }) {
  const [nickname, setNickname] = useState('')
  const [password, setPassword] = useState('')
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')
  // const [suggestions, setSuggestions] = useState([])
  const [success, setSuccess] = useState('')

  const generatePassword = () => {
    const chars = 'abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789!@#$%&*'
    let pass = ''
    for (let i = 0; i < 12; i++) {
      pass += chars[Math.floor(Math.random() * chars.length)]
    }
    setPassword(pass)
  }

  const handleSubmit = async (e) => {
    e.preventDefault()
    if (!nickname.trim()) { setError('Please enter a nickname'); return }
    setLoading(true); setError(''); setSuccess('')
    try {
      const data = await apiFetch('/api/signup', {
        method: 'POST',
        body: JSON.stringify({ nickname: nickname.trim(), password: password })
      })
      // If signup returns token, call onLogin
      if (data.token) {
        onLogin(data.token, data.nickname)
        setSuccess('Account created and logged in')
      } else {
        setSuccess('Account created. Please login')
      }
    } catch (err) {
      // If we received a 409 with suggestions, show them
      if (err && err.status === 409) {
        // setSuggestions(err.payload.suggestions)
        if (err.payload.error === "username_exists") {
          setError('Nickname taken - choose another')
        } else if (err.payload.error === "password_is_vulnerable"){
          setError('Your password exists in a data branch, please take another one')
        }
      } else {
        setError('Server connection error: ' + err.message)
      }
    } finally { setLoading(false) }
  }

  return (
    <div className="signup-container">
      <div className="signup-card">
        <h2>Create Account</h2>
        <form onSubmit={handleSubmit} className="signup-form">
          <div className="form-group">
            <label htmlFor="nickname">Nickname</label>
            <input id="nickname" type="text" value={nickname} onChange={(e) => setNickname(e.target.value)} disabled={loading} />
          </div>

          <div className="form-group">
            <label htmlFor="password">Password</label>
            <div className="password-wrapper">
              <input id="password" type="text" value={password} onChange={(e) => setPassword(e.target.value)} disabled={loading} />
              <button type="button" className="gen-btn" onClick={generatePassword}>Generate</button>
            </div>
          </div>

          {error && <div className="error-message">{error}</div>}
          {success && <div className="success-message">{success}</div>}

          {/* {suggestions.length > 0 && (
            <div className="suggestions">
              <div>Suggestions:</div>
              <ul>
                {suggestions.map((s, idx) => (
                  <li key={idx}><button type="button" onClick={() => setNickname(s)}>{s}</button></li>
                ))}
              </ul>
            </div>
          )} */}

          <div className="button-group">
            <button type="submit" className="signup-button" disabled={loading}>{loading ? 'Creating...' : 'Create Account'}</button>
            <button type="button" className="cancel-button" onClick={onCancel} disabled={loading}>Cancel</button>
          </div>
        </form>
      </div>
    </div>
  )
}

export default SignupPage
