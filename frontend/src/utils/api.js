// Lightweight fetch wrapper that attaches Authorization header when a token exists
export async function apiFetch(path, opts = {}) {
  // base URL can be overridden with Vite env var
  const baseUrl = import.meta.env.VITE_BACKEND_URL || 'http://localhost:8000'
  const url = path.startsWith('http') ? path : `${baseUrl}${path}`

  const headers = {
    ...(opts.headers || {}),
  }

  // If there is a token saved, attach it to the header
  try {
    const token = localStorage.getItem('authToken') || localStorage.getItem('token')
    if (token) headers['Authorization'] = `Bearer ${token}`
  } catch (e) {
    // localStorage may not be available in some contexts; ignore
  }

  // Do not set content-type when body is FormData (browser will set boundary)
  if (opts.body instanceof FormData) {
    // Remove any explicitly set content-type header so browser can add it
    if (headers['Content-Type']) delete headers['Content-Type']
  } else {
    // Ensure we have a sensible default for other calls
    headers['Content-Type'] = headers['Content-Type'] || 'application/json'
  }

  const config = {
    ...opts,
    headers,
  }

  const res = await fetch(url, config)

  // Handle 401 globally: clear token and reload so the app returns to login
  if (res.status === 401) {
    try { localStorage.removeItem('token') } catch (e) {}
    // Refresh to show login screen; keep it simple (App will show login when no token)
    window.location.reload()
    throw new Error('Unauthorized: redirecting to login')
  }

  // Try returning parsed JSON if available, otherwise return raw text
  const contentType = res.headers.get('content-type') || ''
  const isJson = contentType.includes('application/json')
  const payload = isJson ? await res.json() : await res.text()

  if (!res.ok) {
    // If server returns a JSON error with `detail`, forward that
    const message = (payload && payload.detail) ? payload.detail : (payload || res.statusText)
    const err = new Error(message)
    err.status = res.status
    err.payload = payload
    throw err
  }

  return payload
}

export default apiFetch
