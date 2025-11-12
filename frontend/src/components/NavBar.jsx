import './NavBar.css'

function NavBar({ username, currentPage, onNavigate, onLogout }) {
  const handleLogout = () => {
    if (confirm('Are you sure you want to logout?')) {
      onLogout()
    }
  }

  return (
    <nav className="navbar">
      <div className="navbar-container">
        <div className="navbar-brand">
          <h1>🔍 Bloom Filter</h1>
          <span className="subtitle">Quote Search Engine</span>
        </div>

        <ul className="nav-menu">
          <li>
            <button
              className={`nav-link ${currentPage === 'dashboard' ? 'active' : ''}`}
              onClick={() => onNavigate('dashboard')}
            >
              Dashboard
            </button>
          </li>
          <li>
            <button
              className={`nav-link ${currentPage === 'add-book' ? 'active' : ''}`}
              onClick={() => onNavigate('add-book')}
            >
              📚 Add Book
            </button>
          </li>
          <li>
            <button
              className={`nav-link ${currentPage === 'search' ? 'active' : ''}`}
              onClick={() => onNavigate('search')}
            >
              🔎 Search Quotes
            </button>
          </li>
        </ul>

        <div className="navbar-right">
          <span className="username">👤 {username}</span>
          <button className="logout-button" onClick={handleLogout}>
            Logout
          </button>
        </div>
      </div>
    </nav>
  )
}

export default NavBar
