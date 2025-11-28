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
        <svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" className="feather feather-feather"><path d="M20.24 12.24a6 6 0 0 0-8.49-8.49L5 10.5V19h8.5z"></path><line x1="16" y1="8" x2="2" y2="22"></line><line x1="17.5" y1="15" x2="9" y2="15"></line></svg>
          <h1> Smart Writer</h1>
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
          {/* <li>
            <button
              className={`nav-link ${currentPage === 'add-book' ? 'active' : ''}`}
              onClick={() => onNavigate('add-book')}
            >
               Add Book
            </button>
          </li> */}
          <li>
            <button
              className={`nav-link ${currentPage === 'essays' ? 'active' : ''}`}
              onClick={() => onNavigate('essays')}
            >
               Essays
            </button>
          </li>
          {/* <li>
            <button
              className={`nav-link ${currentPage === 'search' ? 'active' : ''}`}
              onClick={() => onNavigate('search')}
            >
               Search Quotes
            </button>
          </li> */}
        </ul>

        <div className="navbar-right">
          <span className="username"> {username}</span>
          <button className="logout-button" onClick={handleLogout}>
            Logout
          </button>
        </div>
      </div>
    </nav>
  )
}

export default NavBar
