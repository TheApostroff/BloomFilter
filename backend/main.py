from fastapi import FastAPI, UploadFile, File, Form, HTTPException, Header
from pydantic import BaseModel
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from typing import Dict, Optional
import os
import secrets
from bloomfilter import BloomFilter
from io import BytesIO
try:
    from docx import Document
except Exception:
    Document = None
try:
    from pypdf import PdfReader
except Exception:
    PdfReader = None
from datetime import datetime
from passlib.hash import pbkdf2_sha256
import re

app = FastAPI()

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# ============ IN-MEMORY STORAGE ============
# În producție, folosiți o bază de date reală
users_db: Dict[str, str] = {}
# For demo: store hashed passwords. In production, use a proper user DB
def add_demo_users():
    users_db["demo"] = pbkdf2_sha256.hash("demo123")
    users_db["user"] = pbkdf2_sha256.hash("pass123")

add_demo_users()

books_db: Dict[int, dict] = {}
bloom_filter = BloomFilter(items_count=50000, fp_prob=0.01)
sessions: Dict[str, str] = {}  # token -> username
next_book_id = 1
next_essay_id = 1

# ============ PYDANTIC MODELS ============
class LoginRequest(BaseModel):
    username: str
    password: str

class QuoteRequest(BaseModel):
    quote: str
    book_title: str

class SearchRequest(BaseModel):
    quote: str


class SignupRequest(BaseModel):
    nickname: str
    password: Optional[str] = None


class EssayRequest(BaseModel):
    title: str
    content: str
    font_size: Optional[int] = 14
    font_style: Optional[str] = 'Arial'

# ============ AUTHENTICATION ENDPOINTS ============
@app.post("/api/auth/login")
async def login(request: LoginRequest):
    """Autentificare utilizator."""
    if request.username not in users_db:
        raise HTTPException(status_code=401, detail="Invalid credentials")
    
    # Verify hashed password (supports pbkdf2_sha256)
    stored = users_db.get(request.username)
    if not stored or not pbkdf2_sha256.verify(request.password, stored):
        raise HTTPException(status_code=401, detail="Invalid credentials")

    # Generează token sigur
    token = secrets.token_urlsafe(32)
    sessions[token] = request.username
    
    return {
        "success": True,
        "token": token,
        "username": request.username
    }

@app.post("/api/auth/logout")
async def logout(token: str = None, authorization: str = Header(None)):
    """Delogare utilizator."""
    # Accept token either as query param or in Authorization header
    if authorization and authorization.lower().startswith("bearer "):
        token = authorization.split(" ", 1)[1]
    if token and token in sessions:
        del sessions[token]
    
    return {"success": True}

@app.get("/api/auth/verify")
async def verify_token(token: str = None, authorization: str = Header(None)):
    """Verifică dacă token-ul este valid."""
    if authorization and authorization.lower().startswith("bearer "):
        token = authorization.split(" ", 1)[1]
    
    return {
        "valid": True,
        "username": sessions[token]
    }

# ============ BOOKS ENDPOINTS ============
@app.get("/api/books")
def list_books(token: str = None, authorization: str = Header(None)):
    """Listează toate cărțile încărcate."""
    if authorization and authorization.lower().startswith("bearer "):
        token = authorization.split(" ", 1)[1]
    # If not authenticated, return an empty result (avoid 401 spam from public clients)
    authenticated = bool(token and token in sessions)
    if not authenticated:
        return {"books": [], "authenticated": False}
    
    return {
        "books": [
            {
                "id": book_id,
                "title": book_data["title"],
                "upload_date": book_data["upload_date"],
                "quotes_count": book_data["quotes_count"]
            } for book_id, book_data in books_db.items()
        ],
        "authenticated": True
    }


def _find_book_entry_by_title(title: str):
    for book_id, book in books_db.items():
        if book.get('title') == title:
            return book_id, book
    return None, None


def _normalize_and_map(raw: str) -> tuple[str, list[int]]:
    """Return (normalized_text, mapping) where mapping[i] is raw index in original text.
    Normalization corresponds to bloom_filter._normalize_text behavior (lowercase, remove punctuation, collapse spaces).
    """
    if raw is None:
        return '', []
    # We'll iterate through raw characters and build normalized output and mapping
    normalized_chars = []
    mapping = []  # maps normalized char index -> raw char index
    last_was_space = False
    for i, ch in enumerate(raw):
        if ch.isalnum() or ch.isspace() or ch == '\n' or ch == '\r':
            if ch.isspace():
                if not last_was_space:
                    normalized_chars.append(' ')
                    mapping.append(i)
                    last_was_space = True
                else:
                    # skip extra whitespace
                    continue
            else:
                normalized_chars.append(ch.lower())
                mapping.append(i)
                last_was_space = False
        else:
            # skip punctuation
            continue
    normalized = ''.join(normalized_chars).strip()
    # Rebuild mapping after strip leading spaces
    # If leading spaces were removed, we need to drop corresponding mapping entries
    leading = 0
    while leading < len(normalized) and normalized[leading] == ' ':
        leading += 1
    if leading > 0:
        normalized = normalized[leading:]
        mapping = mapping[leading:]
    return normalized, mapping


def _extract_all_occurrences(book_entry: dict, query: str) -> list:
    """Find ALL occurrences of query in book_entry raw_text and return list of meta dicts."""
    raw_text = book_entry.get('raw_text')
    if not raw_text:
        return []
    normalized_query = bloom_filter._normalize_text(query)
    normalized_text, mapping = _normalize_and_map(raw_text)
    if not normalized_text:
        return []
    occurrences = []
    start = 0
    while True:
        idx = normalized_text.find(normalized_query, start)
        if idx == -1:
            break
        # Map to raw indices
        start_raw = mapping[idx]
        end_idx = idx + len(normalized_query) - 1
        end_raw = mapping[end_idx] if end_idx < len(mapping) else min(len(raw_text)-1, mapping[-1])
        ctx = 120
        s = max(0, start_raw - ctx)
        e = min(len(raw_text), end_raw + ctx)
        snippet = raw_text[s:e].strip()

        # Paragraph detection
        paragraphs = re.split(r"\n\s*\n", raw_text)
        paragraph_index = 1
        cumulative = 0
        paragraph_start_raw = 0
        paragraph = ''
        for p in paragraphs:
            p_len = len(p)
            if start_raw < cumulative + p_len:
                paragraph = p
                paragraph_start_raw = cumulative
                break
            cumulative += p_len + 2
            paragraph_index += 1
        else:
            paragraph = paragraphs[-1] if paragraphs else ''
            paragraph_start_raw = cumulative

        row = raw_text[paragraph_start_raw:start_raw].count('\n') + 1
        page = None
        if book_entry.get('pages'):
            cum = 0
            for pi, ptext in enumerate(book_entry['pages']):
                if start_raw < cum + len(ptext):
                    page = pi + 1
                    break
                cum += len(ptext) + 2
        if page is None:
            words_before = len(re.findall(r"\w+", raw_text[:start_raw]))
            page = words_before // 300 + 1

        occurrences.append({
            'snippet': snippet,
            'page': page,
            'paragraph': paragraph_index,
            'row': row,
            'start_raw': start_raw,
            'end_raw': end_raw
        })
        start = idx + 1
    return occurrences


def _extract_snippet_and_meta(book_entry: dict, query: str) -> dict | None:
    occs = _extract_all_occurrences(book_entry, query)
    return occs[0] if occs else None

    # end of helper functions

@app.post("/api/books/upload")
async def upload_book(file: UploadFile = File(...), title: str = Form(None), token: str = Form(None), authorization: str = Header(None)):
    """Încarcă o carte text și o indexează în Bloom Filter."""
    global next_book_id
    
    # Accept token either in form field (old) or Authorization header
    if authorization and authorization.lower().startswith("bearer "):
        token = authorization.split(" ", 1)[1]
    if not token or token not in sessions:
        raise HTTPException(status_code=401, detail="Unauthorized")
    
    # Validate file type
    filename = file.filename
    extension = os.path.splitext(filename)[1].lower()
    supported = ['.txt', '.docx', '.pdf']
    if extension not in supported:
        raise HTTPException(status_code=400, detail="Only .txt, .docx or .pdf files allowed")
    
    try:
        content = await file.read()
        text = ''
        pages = None
        if extension == '.pdf':
            if PdfReader is None:
                raise HTTPException(status_code=500, detail='PDF parsing not available (missing pypdf)')
            reader = PdfReader(BytesIO(content))
            page_texts = []
            for p in reader.pages:
                page_texts.append(p.extract_text() or '')
            pages = page_texts
            text = '\n\n'.join(page_texts)
        elif extension == '.docx':
            if Document is None:
                raise HTTPException(status_code=500, detail='DOCX parsing not available (missing python-docx)')
            doc = Document(BytesIO(content))
            paras = [p.text for p in doc.paragraphs]
            text = '\n\n'.join(paras)
        else:
            text = content.decode('utf-8', errors='ignore')
        
        # Utilizează titlul din formular sau extrage din nume fișier
        book_title = title if title else os.path.splitext(file.filename)[0]
        
        # Pre-check if uploaded content is likely duplicated by sampling n-grams and checking BloomFilter hits
        def sample_ngrams(words, min_chunk=2, sample_size=100):
            n = len(words)
            if n <= 0:
                return []
            samples = []
            # sample across different ngram sizes, evenly
            sizes = [min_chunk, 3, 4]
            for sz in sizes:
                if n >= sz:
                    step = max(1, (n - sz + 1) // sample_size)
                    for i in range(0, n - sz + 1, step):
                        samples.append(' '.join(words[i:i+sz]))
            return samples

        norm_text = bloom_filter._normalize_text(text)
        words = norm_text.split()
        samples = sample_ngrams(words, min_chunk=2, sample_size=200)
        if samples:
            hits = 0
            for s in samples:
                if bloom_filter.possibly_contains(s):
                    hits += 1
            duplicate_score = hits / len(samples)
        else:
            duplicate_score = 0.0

        bloom_filter.add_quotes_from_text(text, book_title, chunk_size=20, min_chunk=2, max_chunk=20)
        
        # Stochează informații despre carte (keep raw text and pages if available for snippet extraction)
        book_id = next_book_id
        books_db[book_id] = {
            "title": book_title,
            "filename": file.filename,
            "upload_date": datetime.now().isoformat(),
            "raw_text": text,
            "pages": pages,
            "text_length": len(text),
            "quotes_count": len([q for q in bloom_filter.quotes.keys() if book_title in bloom_filter.quotes[q]])
        }
        next_book_id += 1
        
        return {
            "success": True,
            "book_id": book_id,
            "title": book_title,
            "message": f"Cartea '{book_title}' a fost încărcată cu succes"
            , "duplicate_score": duplicate_score,
            "duplicate": duplicate_score > 0.6
        }
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/books/{book_id}/quotes")
def list_book_quotes(book_id: int, token: str = None, authorization: str = Header(None)):
    """Return the list of normalized quotes associated with a specific book."""
    if authorization and authorization.lower().startswith("bearer "):
        token = authorization.split(" ", 1)[1]
    authenticated = bool(token and token in sessions)

    if book_id not in books_db:
        raise HTTPException(status_code=404, detail="Book not found")

    title = books_db[book_id]['title']
    # scan bloom_filter.quotes for quotes belonging to title
    res = [q for q, titles in bloom_filter.quotes.items() if title in titles]
    return {"quotes": res, "book": title, "authenticated": authenticated}

# ============ QUOTES ENDPOINTS ============
@app.post("/api/quotes/add")
async def add_quote(request: QuoteRequest, token: str = None, authorization: str = Header(None)):
    """Adaugă o citație manuală în Bloom Filter."""
    if authorization and authorization.lower().startswith("bearer "):
        token = authorization.split(" ", 1)[1]
    if not token or token not in sessions:
        raise HTTPException(status_code=401, detail="Unauthorized")
    
    if not request.quote.strip():
        raise HTTPException(status_code=400, detail="Quote cannot be empty")
    
    if not request.book_title.strip():
        raise HTTPException(status_code=400, detail="Book title cannot be empty")
    
    try:
        # pre-check for duplicates
        if bloom_filter.possibly_contains(request.quote):
            # Already present; return conflict
            return JSONResponse(status_code=409, content={"error": "duplicate", "message": "Quote already exists"})
        bloom_filter.add(request.quote, request.book_title)
        
        return {
            "success": True,
            "message": f"Citația a fost adăugată din cartea '{request.book_title}'"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post('/api/essays')
def create_essay(request: EssayRequest, token: str = None, authorization: str = Header(None)):
    """Create a new essay in user's library. Requires authentication."""
    global next_essay_id
    if authorization and authorization.lower().startswith("bearer "):
        token = authorization.split(" ", 1)[1]
    if not token or token not in sessions:
        raise HTTPException(status_code=401, detail="Unauthorized")
    try:
        essay_id = next_essay_id
        essays_db[essay_id] = {
            'id': essay_id,
            'title': request.title,
            'content': request.content,
            'font_size': request.font_size,
            'font_style': request.font_style,
            'author': sessions[token],
            'created_at': datetime.now().isoformat(),
            'updated_at': datetime.now().isoformat()
        }
        next_essay_id += 1
        return { 'ok': True, 'essay_id': essay_id, 'essay': essays_db[essay_id] }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get('/api/essays')
def list_essays(token: str = None, authorization: str = Header(None)):
    """List authored essays for authenticated user."""
    if authorization and authorization.lower().startswith("bearer "):
        token = authorization.split(" ", 1)[1]
    if not token or token not in sessions:
        # return empty library for unauthenticated users
        return {'essays': [], 'authenticated': False}
    author = sessions[token]
    res = [e for e in essays_db.values() if e.get('author') == author]
    return {'essays': res, 'authenticated': True}


@app.get('/api/essays/{essay_id}')
def get_essay(essay_id: int, token: str = None, authorization: str = Header(None)):
    if authorization and authorization.lower().startswith("bearer "):
        token = authorization.split(" ", 1)[1]
    if essay_id not in essays_db:
        raise HTTPException(status_code=404, detail='Essay not found')
    essay = essays_db[essay_id]
    # public read: return essay if it belongs to author or if authenticated
    if not token or token not in sessions:
        return {'essay': essay, 'authenticated': False}
    if essays_db[essay_id].get('author') != sessions[token]:
        # unauthorized to edit, but read allowed
        return {'essay': essay, 'authenticated': True, 'owner': False}
    return {'essay': essay, 'authenticated': True, 'owner': True}


@app.put('/api/essays/{essay_id}')
def update_essay(essay_id: int, request: EssayRequest, token: str = None, authorization: str = Header(None)):
    if authorization and authorization.lower().startswith("bearer "):
        token = authorization.split(" ", 1)[1]
    if not token or token not in sessions:
        raise HTTPException(status_code=401, detail='Unauthorized')
    if essay_id not in essays_db:
        raise HTTPException(status_code=404, detail='Essay not found')
    if essays_db[essay_id].get('author') != sessions[token]:
        raise HTTPException(status_code=403, detail='Forbidden')
    essays_db[essay_id].update({
        'title': request.title,
        'content': request.content,
        'font_size': request.font_size,
        'font_style': request.font_style,
        'updated_at': datetime.now().isoformat()
    })
    return {'ok': True, 'essay': essays_db[essay_id]}


@app.delete('/api/essays/{essay_id}')
def delete_essay(essay_id: int, token: str = None, authorization: str = Header(None)):
    if authorization and authorization.lower().startswith("bearer "):
        token = authorization.split(" ", 1)[1]
    if not token or token not in sessions:
        raise HTTPException(status_code=401, detail='Unauthorized')
    if essay_id not in essays_db:
        raise HTTPException(status_code=404, detail='Essay not found')
    if essays_db[essay_id].get('author') != sessions[token]:
        raise HTTPException(status_code=403, detail='Forbidden')
    del essays_db[essay_id]
    return {'ok': True}

@app.post("/api/quotes/search")
async def search_quote(request: SearchRequest, token: str = None, authorization: str = Header(None)):
    """Caută o citație în Bloom Filter."""
    if authorization and authorization.lower().startswith("bearer "):
        token = authorization.split(" ", 1)[1]
    if not token or token not in sessions:
        raise HTTPException(status_code=401, detail="Unauthorized")
    
    if not request.quote.strip():
        raise HTTPException(status_code=400, detail="Quote cannot be empty")
    
    try:
        possibly_present = bloom_filter.possibly_contains(request.quote)
        
        if possibly_present:
            titles = bloom_filter.get_quote_source(request.quote)
            occurrences = []
            for title in titles:
                bid, book = _find_book_entry_by_title(title)
                if book:
                    # Return all occurrences for this title
                    occs = _extract_all_occurrences(book, request.quote)
                    if occs:
                        for o in occs:
                            occurrences.append({
                                'title': title,
                                'page': o['page'],
                                'paragraph': o['paragraph'],
                                'row': o['row'],
                                'snippet': o['snippet']
                            })
                    else:
                        occurrences.append({'title': title})
                else:
                    occurrences.append({'title': title})
            return {
                "found": True,
                "message": "Citația ar putea fi prezentă",
                "sources": occurrences if occurrences else ["Posibilă prezență - false positive"],
                "authenticated": bool(token and token in sessions)
            }
        else:
            return {
                "found": False,
                "message": "Citația sigur NU este prezentă în baza de date",
                "sources": [],
                "authenticated": bool(token and token in sessions)
            }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# ============ BLOOM FILTER STATS ============
@app.get("/api/bloom-filter/stats")
async def get_bloom_stats(token: str = None, authorization: str = Header(None)):
    """Returnează statistici despre Bloom Filter."""
    if authorization and authorization.lower().startswith("bearer "):
        token = authorization.split(" ", 1)[1]
    authenticated = bool(token and token in sessions)
    
    stats = bloom_filter.get_stats()
    return {
        "stats": stats,
        "total_books": len(books_db),
        "authenticated": authenticated
    }

# ============ HEALTH CHECK ============
@app.get("/api/health")
def health_check():
    """Verifică starea API-ului."""
    # Simple health endpoint; extend as needed with deeper checks
    return {"status": "ok"}

@app.get("/api/search")
def search(word: str):
    # res = search_word(db, word)
    res = []
    # attach snippets: for each result compute snippet from stored path or DB (if pos offset known)
    # for r in res:
    #     # build snippets safely:
    #     r['snippets'] = []
    #     try:
    #         book = db.get_book(r['book_id'])
    #         if book and book[2] and os.path.exists(book[2]):
    #             with open(book[2],'r',encoding='utf-8',errors='ignore') as f:
    #                 text = f.read()
    #             for pos in r['positions'][:5]:
    #                 # pos is token index; to get offset we may store offsets in index - if not, just show small excerpt
    #                 off = 0
    #                 # naive snippet: search first occurrence of the word
    #                 idx = text.lower().find(word.lower())
    #                 if idx!=-1:
    #                     start = max(0, idx-30)
    #                     r['snippets'].append(text[start: start+160].replace('\n',' '))
    #     except Exception:
    #         pass
    return res

@app.post("/api/signup")
def signup(request: SignupRequest):
    nick = request.nickname.strip()
    if not nick:
        return JSONResponse(status_code=400, content={"error":"nick required"})
    # If nickname already exists, provide suggestions
    if nick in users_db:
        # generate suggestions
        def suggest_variants(base, n=4):
            out = []
            for i in range(n):
                out.append(f"{base}{secrets.choice('0123456789')}{secrets.choice('0123456789')}")
            return out
        suggestions = suggest_variants(nick, 4)
        return JSONResponse(status_code=409, content={"error":"taken", "suggestions": suggestions})
    # determine password
    password = request.password if request.password else secrets.token_urlsafe(10)
    # store hashed password
    users_db[nick] = pbkdf2_sha256.hash(password)
    # create a session token and return it
    token = secrets.token_urlsafe(32)
    sessions[token] = nick
    return {"ok": True, "nickname": nick, "password": password, "token": token}
    # if db.get_user_by_nickname(nick):
        # suggestions = suggest_nick_variants(nick, {}, db, max_suggestions=5)
        # suggestions = ""
        # return JSONResponse(status_code=409, content={"error":"taken", "suggestions": suggestions})
    # db.add_user(nick, {})
    return {"ok": True}
