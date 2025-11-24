import { useState, useEffect } from 'react'
import './App.css'
import LoginPage from './pages/LoginPage'
import Dashboard from './pages/Dashboard'
import AddBook from './pages/AddBook'
import SearchQuotes from './pages/SearchQuotes'
import NavBar from './components/NavBar'

function App() {
  const [currentPage, setCurrentPage] = useState('login')
  const [token, setToken] = useState(null)
  const [username, setUsername] = useState(null)

  // Verifică dacă utilizatorul este deja logat
  useEffect(() => {
    const storedToken = localStorage.getItem('authToken')
    const storedUsername = localStorage.getItem('username')
    
    if (storedToken && storedUsername) {
      setToken(storedToken)
      setUsername(storedUsername)
      setCurrentPage('dashboard')
    }
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
    return <LoginPage onLogin={handleLogin} />
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
      </main>
    </div>
  )
}

export default App
