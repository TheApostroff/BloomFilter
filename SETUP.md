# Instrucțiuni de rulare a Bloom Filter Quote Search Engine

> Recommended: Use Python 3.11 or 3.12 for development. This repo targets Python >= 3.11.

## Pentru Windows (PowerShell)

### 1. Terminal 1 - Backend

```powershell
cd backend
# create virtual environment (.venv) and activate it
python -m venv .venv
. .venv\Scripts\Activate.ps1
# install runtime deps
python -m pip install -U pip
python -m pip install -r requirements.txt
# run the backend app
python -m uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

### Troubleshooting backend startup (pydantic_core / import errors)

- If the server fails to start with an error like `ModuleNotFoundError: No module named 'pydantic_core._pydantic_core'`, confirm the following steps:

	1. Check Python version used in the virtual environment. You should be using Python 3.11+:
	```powershell
	python -V
	```

	2. Ensure you're using the virtual environment where the packages were installed:
	```powershell
	. .venv\Scripts\Activate.ps1
	python -m pip show pydantic
	python -m pip show pydantic-core
	```

	3. If `pydantic` shows installed but `pydantic_core._pydantic_core` cannot be imported, reinstall the packages to force correct binary wheel for your platform and Python version:
	```powershell
	python -m pip install --upgrade --force-reinstall pydantic pydantic-core
	```

	3a. You can validate the native module is importable from the active interpreter:
	```powershell
	python -c "import pydantic_core; print(pydantic_core.__file__)"
	python -c "import importlib; importlib.import_module('pydantic_core._pydantic_core'); print('native module loaded ok')"
	```

	4. Some platforms (older Python versions or missing build toolchain) may try to compile `pydantic-core` from source, which requires Rust and is not recommended for a simple dev setup. Use a supported Python version (3.11 or 3.12) and let pip install a pre-built wheel.

	5. If the problem persists, check for multiple Python installations or user-site packages interfering with the venv. Prefer `python -m pip` and do not use `pip` from PATH directly.

	5a. You can try pinning compatible versions (example):
	```powershell
	python -m pip uninstall -y pydantic pydantic-core
	python -m pip install pydantic==2.12.4 pydantic-core==2.41.5
	```

	6. After reinstalling, verify the server runs and health endpoint responds:
	```powershell
	python -m uvicorn main:app --reload --host 0.0.0.0 --port 8000
	# then in another terminal, check the health
	curl http://localhost:8000/api/health
	```

### Troubleshooting frontend "Failed to fetch"

- If the frontend shows "Error loading data: Failed to fetch", it typically means the frontend couldn't reach the backend or the response was blocked (CORS or server error). Try the following steps:

	1. Confirm the backend is running and healthy:
	```powershell
	curl http://localhost:8000/api/health
	```

	2. Check the browser developer console (Network tab) for the failing request: it will show if the request was blocked by CORS (check Response headers) or if the server returned an HTTP error (5xx/4xx).

	3. Try calling the endpoint directly from PowerShell to isolate the problem from the frontend:
	```powershell
	# Get books (replace $token with the token value)
	Invoke-RestMethod -Uri 'http://localhost:8000/api/books' -Headers @{Authorization = "Bearer $token"}
	```

	4. If CORS is the problem, ensure the backend CORS middleware is configured to allow the frontend origin or all origins during dev. In `backend/main.py` we already set `allow_origins=['*']` for ease.

	5. If the server logs show Python import errors or other exceptions, fix those first and reload uvicorn. If the server cannot start, the frontend cannot fetch data.

	6. If the server is healthy and calls work from curl but the frontend still fails, check that the frontend is calling the correct backend URL & port (http vs https).

### 2. Terminal 2 - Frontend

```powershell
cd frontend
npm install
npm run dev
```

### One-command dev startup (Windows PowerShell)

Use the `start-all.ps1` at the repo root to open two PowerShell windows and start backend & frontend automatically:

```powershell
.\start-all.ps1
```

> Note: If PowerShell refuses to run scripts, set the execution policy for the current process (only affects current shell):
```powershell
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope Process
```

If you encounter errors on startup (e.g. package binary compatibility issues), force reinstall backend dependencies and verify environment:
```powershell
cd backend
. .venv\Scripts\Activate.ps1
.\start-backend.ps1 -Reinstall
# or manually reinstall and run the server:
python -m pip install --upgrade --force-reinstall -r requirements.txt
python -m uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

## Pentru macOS/Linux

### 1. Terminal 1 - Backend

```bash
cd backend
python -m venv .venv
source .venv/bin/activate
python -m pip install -U pip
python -m pip install -r requirements.txt
python -m uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

### 2. Terminal 2 - Frontend

```bash
cd frontend
npm run dev
```

### One-command dev startup (macOS/Linux)

Use the `start-all.sh` at the repo root to start backend & frontend in parallel:

```bash
./start-all.sh
```

If the script is not executable, make it so once:
```bash
chmod +x start-all.sh backend/start-backend.sh frontend/start-frontend.sh
```

## Acces

- **Frontend**: http://localhost:5173
- **Backend API**: http://localhost:8000
- **API Documentation**: http://localhost:8000/docs

## Credențiale Demo

- **Username**: demo
- **Password**: demo123

## Fișiere Teste

Poți folosi orice fișier .txt pentru testing. Exemple:
- Shakespeare quotes
- Gutenberg Project books
- Propriile fișiere text

---

Odată ce ambele servere rulează, acces frontend-ul și logheaza-te cu credentialele demo!

## Notes on auth

- The API now expects an Authorization header: `Authorization: Bearer <token>` for protected endpoints (books, upload, quotes, stats, etc.).
- Tokens are returned by the `/api/auth/login` endpoint and are secure random tokens (not JWT in this demo).

### Frontend global fetch helper

- The frontend includes a lightweight helper `frontend/src/utils/api.js` named `apiFetch` that automatically attaches the `Authorization: Bearer <token>` header when a token exists in `localStorage` under the key `authToken` (also falls back to `token`).
- The `apiFetch` also handles 401 responses by clearing the token and reloading the app so the login screen is shown. This helps avoid repeated 401 log entries from unauthenticated fetches in dev.

If you override or extend the frontend, prefer using `apiFetch('/api/your-path', opts)` instead of raw `fetch()` so the token/header handling is consistent.

## Notes on indexing & searching

- When you upload a text file, the backend will index it into the Bloom Filter by extracting n-grams (substrings of adjacent words). To keep indexing responsive, the default behavior indexes n-grams between 2 and 20 words (per upload); you can change this in the server call `bloom_filter.add_quotes_from_text(text, book_title, chunk_size, min_chunk=2, max_chunk=20)` in `backend/main.py`.
- Shorter quotes (2-3 words) are now indexed and searchable, and the search normalizes punctuation and whitespace so capitalization or punctuation won't prevent matches.
- The demo still uses an in-memory session store and is not persistent across server restarts. For production, consider using a DB and JWT for stateless tokens.

## PDF/DOCX upload and Snippet Results

- The backend supports `.txt`, `.docx`, and `.pdf` uploads. For PDFs, the app will extract text per page and attempt to return a page number for found quotes. For .docx files, the document is read paragraph-by-paragraph.
- Search results now include `sources` objects with the following fields (when available): `title`, `page`, `paragraph`, `row`, and `snippet`. The `snippet` provides an excerpt of the surrounding text for easier verification.
- The following Python packages are required for PDF/DOCX support: `python-docx` and `pypdf`. They are in `backend/requirements.txt` and will be installed when you run the standard installation steps.

## Quick API examples (PowerShell)

1) Login and get token

```powershell
$resp = Invoke-RestMethod -Uri 'http://localhost:8000/api/auth/login' -Method Post -ContentType 'application/json' -Body (@{username='demo'; password='demo123'} | ConvertTo-Json)
$token = $resp.token
Write-Host "Token: $token"
```

2) List books (GET)

```powershell
Invoke-RestMethod -Uri 'http://localhost:8000/api/books' -Headers @{Authorization = "Bearer $token"}
```

3) Upload a book (multipart/form-data)

```powershell
Invoke-RestMethod -Uri 'http://localhost:8000/api/books/upload' -Method Post -Headers @{Authorization = "Bearer $token"} -Form @{file = Get-Item 'C:\path\to\book.txt'; title = 'My Book'}
```

4) Search a quote (POST JSON)

```powershell
Invoke-RestMethod -Uri 'http://localhost:8000/api/quotes/search' -Method Post -ContentType 'application/json' -Headers @{Authorization = "Bearer $token"} -Body (@{quote='Hello world'} | ConvertTo-Json)
```

5) Add a quote (POST JSON)

```powershell
Invoke-RestMethod -Uri 'http://localhost:8000/api/quotes/add' -Method Post -ContentType 'application/json' -Headers @{Authorization = "Bearer $token"} -Body (@{quote='Hello world'; book_title='My Book'} | ConvertTo-Json)
```

## Quick API examples (cURL - Linux/macOS)

1) Login

```bash
curl -X POST http://localhost:8000/api/auth/login -H 'Content-Type: application/json' -d '{"username":"demo","password":"demo123"}'
```

2) List books

```bash
curl -H "Authorization: Bearer <token>" http://localhost:8000/api/books
```

3) Upload a book (curl multipart)

```bash
curl -X POST -H "Authorization: Bearer <token>" -F "file=@/path/to/book.txt" -F "title=My Book" http://localhost:8000/api/books/upload
```

4) Search a quote

```bash
curl -X POST -H "Authorization: Bearer <token>" -H "Content-Type: application/json" -d '{"quote":"Hello world"}' http://localhost:8000/api/quotes/search
```

5) Add a quote

```bash
curl -X POST -H "Authorization: Bearer <token>" -H "Content-Type: application/json" -d '{"quote":"Hello world","book_title":"My Book"}' http://localhost:8000/api/quotes/add
```

## Running tests (backend)

```powershell
cd backend
. .venv\Scripts\Activate.ps1
python -m pip install -r requirements-dev.txt
python -m pytest -q
```

or (Linux/macOS)

```bash
cd backend
source .venv/bin/activate
python -m pip install -r requirements-dev.txt
python -m pytest -q
```

## Notes & troubleshooting
- The demo uses an in-memory users/sessions store; it is NOT persistent across server restarts.
- For production use, replace the in-memory stores with a real database and use secure token management or JWTs with expiry/refresh.
- If you prefer to install dependencies from `pyproject.toml` directly, you can use `pip install -e .` inside the `backend` folder (needs a valid build backend configuration).
