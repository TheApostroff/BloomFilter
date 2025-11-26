import { useState, useEffect } from 'react'
import apiFetch from './utils/api'
import './App.css'
import LoginPage from './pages/LoginPage'
import SignupPage from './pages/SignupPage'
import Dashboard from './pages/Dashboard'
import AddBook from './pages/AddBook'
import SearchQuotes from './pages/SearchQuotes'
import NavBar from './components/NavBar'
import Essays from './pages/Essays'
import EssayEditor from './pages/EssayEditor'

function App() {
  const [currentPage, setCurrentPage] = useState('login')
  const [token, setToken] = useState(null)
  const [username, setUsername] = useState(null)

  // Verifică dacă utilizatorul este deja logat
  useEffect(() => {
    const verifyToken = async () => {
      const storedToken = localStorage.getItem('authToken')
      const storedUsername = localStorage.getItem('username')
      if (storedToken && storedUsername) {
        // verify with backend
        try {
          const res = await fetch(`${import.meta.env.VITE_BACKEND_URL || 'http://localhost:8000'}/api/auth/verify`, { headers: { 'Authorization': `Bearer ${storedToken}` } })
          if (res.ok) {
            setToken(storedToken)
            setUsername(storedUsername)
            setCurrentPage('dashboard')
          } else {
            localStorage.removeItem('authToken')
            localStorage.removeItem('username')
          }
        } catch (err) {
          // network error; keep client UI in login state
          localStorage.removeItem('authToken')
          localStorage.removeItem('username')
        }
      }
    }
    verifyToken()
  }, [])

  const handleLogin = (newToken, newUsername) => {
    setToken(newToken)
    setUsername(newUsername)
    localStorage.setItem('authToken', newToken)
    localStorage.setItem('username', newUsername)
    setCurrentPage('dashboard')
  }

  const handleLogout = () => {
    localStorage.removeItem('authToken')
    localStorage.removeItem('username')
    setToken(null)
    setUsername(null)
    setCurrentPage('login')
  }

  if (!token) {
    return (
      currentPage === 'signup'
      ? <SignupPage onLogin={handleLogin} onCancel={() => setCurrentPage('login')} />
      : <LoginPage onLogin={handleLogin} onShowSignup={() => setCurrentPage('signup')} />
    )
  }

  return (
    <div className="app-container">
      <NavBar 
        username={username} 
        currentPage={currentPage}
        onNavigate={setCurrentPage}
        onLogout={handleLogout}
      />
      
      <main className="main-content">
        {currentPage === 'dashboard' && (
          <Dashboard token={token} />
        )}
        
        {currentPage === 'add-book' && (
          <AddBook token={token} onSuccess={() => setCurrentPage('dashboard')} />
        )}
        
        {currentPage === 'search' && (
          <SearchQuotes token={token} />
        )}
        {currentPage === 'essays' && (
          <Essays token={token} onNavigate={setCurrentPage} />
        )}
        {currentPage === 'essay-editor' && (
          <EssayEditor token={token} onNavigate={setCurrentPage} />
        )}
      </main>
    </div>
  )
}

export default App
