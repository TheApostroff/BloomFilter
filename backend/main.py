from fastapi import FastAPI, UploadFile, File, Form, HTTPException
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Dict, List, Optional
import json
import os
from bloom_filter import BloomFilter
from datetime import datetime

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
users_db: Dict[str, str] = {
    "demo": "demo123",
    "user": "pass123"
}

books_db: Dict[int, dict] = {}
bloom_filter = BloomFilter(size=50000, num_hashes=3)
sessions: Dict[str, str] = {}  # token -> username
next_book_id = 1

# ============ PYDANTIC MODELS ============
class LoginRequest(BaseModel):
    username: str
    password: str

class QuoteRequest(BaseModel):
    quote: str
    book_title: str

class SearchRequest(BaseModel):
    quote: str

# ============ AUTHENTICATION ENDPOINTS ============
@app.post("/api/auth/login")
async def login(request: LoginRequest):
    """Autentificare utilizator."""
    if request.username not in users_db:
        raise HTTPException(status_code=401, detail="Invalid credentials")
    
    if users_db[request.username] != request.password:
        raise HTTPException(status_code=401, detail="Invalid credentials")
    
    # Generează token simplu
    token = f"{request.username}_{datetime.now().timestamp()}"
    sessions[token] = request.username
    
    return {
        "success": True,
        "token": token,
        "username": request.username
    }

@app.post("/api/auth/logout")
async def logout(token: str = None):
    """Delogare utilizator."""
    if token and token in sessions:
        del sessions[token]
    
    return {"success": True}

@app.get("/api/auth/verify")
async def verify_token(token: str = None):
    """Verifică dacă token-ul este valid."""
    if not token or token not in sessions:
        raise HTTPException(status_code=401, detail="Unauthorized")
    
    return {
        "valid": True,
        "username": sessions[token]
    }

# ============ BOOKS ENDPOINTS ============
@app.get("/api/books")
def list_books(token: str = None):
    """Listează toate cărțile încărcate."""
    if not token or token not in sessions:
        raise HTTPException(status_code=401, detail="Unauthorized")
    
    return {
        "books": [
            {
                "id": book_id,
                "title": book_data["title"],
                "upload_date": book_data["upload_date"],
                "quotes_count": book_data["quotes_count"]
            }
            for book_id, book_data in books_db.items()
        ]
    }

@app.post("/api/books/upload")
async def upload_book(file: UploadFile = File(...), title: str = Form(None), token: str = Form(None)):
    """Încarcă o carte text și o indexează în Bloom Filter."""
    global next_book_id
    
    if not token or token not in sessions:
        raise HTTPException(status_code=401, detail="Unauthorized")
    
    # Validează tipul fișierului
    if not file.filename.lower().endswith('.txt'):
        raise HTTPException(status_code=400, detail="Only .txt files allowed")
    
    try:
        content = await file.read()
        text = content.decode('utf-8', errors='ignore')
        
        # Utilizează titlul din formular sau extrage din nume fișier
        book_title = title if title else os.path.splitext(file.filename)[0]
        
        # Adaugă citate în Bloom Filter
        bloom_filter.add_quotes_from_text(text, book_title, chunk_size=50)
        
        # Stochează informații despre carte
        book_id = next_book_id
        books_db[book_id] = {
            "title": book_title,
            "filename": file.filename,
            "upload_date": datetime.now().isoformat(),
            "text_length": len(text),
            "quotes_count": len([q for q in bloom_filter.quotes.keys() if book_title in bloom_filter.quotes[q]])
        }
        next_book_id += 1
        
        return {
            "success": True,
            "book_id": book_id,
            "title": book_title,
            "message": f"Cartea '{book_title}' a fost încărcată cu succes"
        }
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# ============ QUOTES ENDPOINTS ============
@app.post("/api/quotes/add")
async def add_quote(request: QuoteRequest, token: str = None):
    """Adaugă o citație manuală în Bloom Filter."""
    if not token or token not in sessions:
        raise HTTPException(status_code=401, detail="Unauthorized")
    
    if not request.quote.strip():
        raise HTTPException(status_code=400, detail="Quote cannot be empty")
    
    if not request.book_title.strip():
        raise HTTPException(status_code=400, detail="Book title cannot be empty")
    
    try:
        bloom_filter.add(request.quote, request.book_title)
        
        return {
            "success": True,
            "message": f"Citația a fost adăugată din cartea '{request.book_title}'"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/quotes/search")
async def search_quote(request: SearchRequest, token: str = None):
    """Caută o citație în Bloom Filter."""
    if not token or token not in sessions:
        raise HTTPException(status_code=401, detail="Unauthorized")
    
    if not request.quote.strip():
        raise HTTPException(status_code=400, detail="Quote cannot be empty")
    
    try:
        possibly_present = bloom_filter.possibly_contains(request.quote)
        
        if possibly_present:
            sources = bloom_filter.get_quote_source(request.quote)
            return {
                "found": True,
                "message": "Citația ar putea fi prezentă",
                "sources": sources if sources else ["Posibilă prezență - false positive"]
            }
        else:
            return {
                "found": False,
                "message": "Citația sigur NU este prezentă în baza de date",
                "sources": []
            }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# ============ BLOOM FILTER STATS ============
@app.get("/api/bloom-filter/stats")
async def get_bloom_stats(token: str = None):
    """Returnează statistici despre Bloom Filter."""
    if not token or token not in sessions:
        raise HTTPException(status_code=401, detail="Unauthorized")
    
    stats = bloom_filter.get_stats()
    return {
        "stats": stats,
        "total_books": len(books_db)
    }

# ============ HEALTH CHECK ============
@app.get("/api/health")
def health_check():
    """Verifică starea API-ului."""
    return {"status": "ok"}
    # LanguageTool can auto-detect or set language; we call tool.check
    try:
        matches = tool.check(text)
    except Exception as e:
        # fallback: return empty
        return {"issues": []}
    issues = []
    for m in matches:
        # each match has offset, errorLength, message, replacements
        issues.append({
            "offset": m.offset,
            "length": m.errorLength,
            "message": m.message,
            "replacements": m.replacements
        })
    return {"issues": issues}

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
def signup(payload: dict):
    nick = payload.get('nickname','').strip()
    if not nick:
        return JSONResponse(status_code=400, content={"error":"nick required"})
    # if db.get_user_by_nickname(nick):
        # suggestions = suggest_nick_variants(nick, {}, db, max_suggestions=5)
        # suggestions = ""
        # return JSONResponse(status_code=409, content={"error":"taken", "suggestions": suggestions})
    # db.add_user(nick, {})
    return {"ok": True}
