from fastapi import FastAPI, HTTPException, Header
from pydantic import BaseModel
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from typing import Optional
from typing import List
import secrets
from bloomfilter import BloomFilter
from passwordcheck import BF as passcheck
from spellcheck.spellcheck import check_word as spell_check_word

try:
    from docx import Document
except Exception:
    Document = None
try:
    from pypdf import PdfReader
except Exception:
    PdfReader = None
from passlib.hash import pbkdf2_sha256

import sqlite3

connection = sqlite3.connect("db.db", check_same_thread=False)

connection.execute("""
CREATE TABLE IF NOT EXISTS Users(
    id INTEGER PRIMARY KEY,
    username TEXT NOT NULL,
    password TEXT NOT NULL,
    session TEXT NOT NULL
)
""")

connection.execute("""
CREATE TABLE IF NOT EXISTS Sessions(
    token TEXT PRIMARY KEY,
    username TEXT NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
)
""")

connection.execute("""
CREATE TABLE IF NOT EXISTS Essays(
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    title TEXT NOT NULL,
    content TEXT NOT NULL,
    font_size INTEGER DEFAULT 14,
    font_style TEXT DEFAULT 'Arial',
    author TEXT NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
)
""")

connection.commit()

users = connection.execute("SELECT username FROM Users").fetchall()
username_checker = BloomFilter(len(users) * 2 + 10_000, 0.01)
for user in users:
    username = user[0]
    username_checker.add(username)

app = FastAPI()

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


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
    font_style: Optional[str] = "Arial"


class SpellCheckRequest(BaseModel):
    # Accept either raw text or an explicit list of words
    text: Optional[str] = None
    words: Optional[List[str]] = None

class SpellCheckItem(BaseModel):
    value: str
    normalize: str
    valid: bool


# ============ AUTHENTICATION ENDPOINTS ============
@app.post("/api/auth/login")
async def login(request: LoginRequest):
    """Autentificare utilizator."""
    user = connection.execute(
        "SELECT username, password FROM Users WHERE username=?", (request.username,)
    ).fetchone()

    username, password = user
    if not user or request.username != username:
        raise HTTPException(status_code=401, detail="Invalid credentials")

    if not pbkdf2_sha256.verify(request.password, password):
        raise HTTPException(status_code=402, detail="Invalid credentials")

    token = secrets.token_urlsafe(32)
    connection.execute(
        "INSERT INTO Sessions(token, username) VALUES(?,?)", (token, request.username)
    )
    connection.commit()

    return {"success": True, "token": token, "username": request.username}


@app.post("/api/auth/logout")
async def logout(token: str = None, authorization: str = Header(None)):
    """Delogare utilizator."""
    # Accept token either as query param or in Authorization header
    if authorization and authorization.lower().startswith("bearer "):
        token = authorization.split(" ", 1)[1]
    if token:
        connection.execute("DELETE FROM Sessions WHERE token=?", (token,))
        connection.commit()

    return {"success": True}


@app.get("/api/auth/verify")
async def verify_token(token: str = None, authorization: str = Header(None)):
    """Verifică dacă token-ul este valid."""
    if authorization and authorization.lower().startswith("bearer "):
        token = authorization.split(" ", 1)[1]

    if token:
        result = connection.execute(
            "SELECT username FROM Sessions WHERE token=?", (token,)
        ).fetchone()
        if result:
            return {"valid": True, "username": result[0]}
    return {"valid": False, "username": ""}


@app.post("/api/essays")
def create_essay(
    request: EssayRequest, token: str = None, authorization: str = Header(None)
):
    """Create a new essay in user's library. Requires authentication."""
    if authorization and authorization.lower().startswith("bearer "):
        token = authorization.split(" ", 1)[1]

    username = None
    if token:
        result = connection.execute(
            "SELECT username FROM Sessions WHERE token=?", (token,)
        ).fetchone()
        if result:
            username = result[0]

    if not username:
        raise HTTPException(status_code=401, detail="Unauthorized")

    try:
        connection.execute(
            """
            INSERT INTO Essays(title, content, font_size, font_style, author)
            VALUES(?, ?, ?, ?, ?)
            """,
            (
                request.title,
                request.content,
                request.font_size,
                request.font_style,
                username,
            ),
        )
        connection.commit()
        essay_id = connection.lastrowid

        essay = connection.execute(
            "SELECT id, title, content, font_size, font_style, author, created_at, updated_at FROM Essays WHERE id=?",
            (essay_id,),
        ).fetchone()

        return {
            "ok": True,
            "essay_id": essay_id,
            "essay": {
                "id": essay[0],
                "title": essay[1],
                "content": essay[2],
                "font_size": essay[3],
                "font_style": essay[4],
                "author": essay[5],
                "created_at": essay[6],
                "updated_at": essay[7],
            },
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/essays")
def list_essays(token: str = None, authorization: str = Header(None)):
    """List authored essays for authenticated user."""
    if authorization and authorization.lower().startswith("bearer "):
        token = authorization.split(" ", 1)[1]

    author = None
    if token:
        result = connection.execute(
            "SELECT username FROM Sessions WHERE token=?", (token,)
        ).fetchone()
        if result:
            author = result[0]

    if not author:
        # return empty library for unauthenticated users
        return {"essays": [], "authenticated": False}

    essays = connection.execute(
        "SELECT id, title, content, font_size, font_style, author, created_at, updated_at FROM Essays WHERE author=?",
        (author,),
    ).fetchall()

    res = [
        {
            "id": e[0],
            "title": e[1],
            "content": e[2],
            "font_size": e[3],
            "font_style": e[4],
            "author": e[5],
            "created_at": e[6],
            "updated_at": e[7],
        }
        for e in essays
    ]

    return {"essays": res, "authenticated": True}


@app.get("/api/essays/{essay_id}")
def get_essay(essay_id: int, token: str = None, authorization: str = Header(None)):
    if authorization and authorization.lower().startswith("bearer "):
        token = authorization.split(" ", 1)[1]

    essay_data = connection.execute(
        "SELECT id, title, content, font_size, font_style, author, created_at, updated_at FROM Essays WHERE id=?",
        (essay_id,),
    ).fetchone()

    if not essay_data:
        raise HTTPException(status_code=404, detail="Essay not found")

    essay = {
        "id": essay_data[0],
        "title": essay_data[1],
        "content": essay_data[2],
        "font_size": essay_data[3],
        "font_style": essay_data[4],
        "author": essay_data[5],
        "created_at": essay_data[6],
        "updated_at": essay_data[7],
    }

    username = None
    if token:
        result = connection.execute(
            "SELECT username FROM Sessions WHERE token=?", (token,)
        ).fetchone()
        if result:
            username = result[0]

    # public read: return essay if it belongs to author or if authenticated
    if not username:
        return {"essay": essay, "authenticated": False}
    if essay["author"] != username:
        # unauthorized to edit, but read allowed
        return {"essay": essay, "authenticated": True, "owner": False}
    return {"essay": essay, "authenticated": True, "owner": True}


@app.put("/api/essays/{essay_id}")
def update_essay(
    essay_id: int,
    request: EssayRequest,
    token: str = None,
    authorization: str = Header(None),
):
    if authorization and authorization.lower().startswith("bearer "):
        token = authorization.split(" ", 1)[1]

    username = None
    if token:
        result = connection.execute(
            "SELECT username FROM Sessions WHERE token=?", (token,)
        ).fetchone()
        if result:
            username = result[0]

    if not username:
        raise HTTPException(status_code=401, detail="Unauthorized")

    essay_data = connection.execute(
        "SELECT author FROM Essays WHERE id=?", (essay_id,)
    ).fetchone()

    if not essay_data:
        raise HTTPException(status_code=404, detail="Essay not found")
    if essay_data[0] != username:
        raise HTTPException(status_code=403, detail="Forbidden")

    connection.execute(
        """
        UPDATE Essays
        SET title=?, content=?, font_size=?, font_style=?, updated_at=CURRENT_TIMESTAMP
        WHERE id=?
        """,
        (
            request.title,
            request.content,
            request.font_size,
            request.font_style,
            essay_id,
        ),
    )
    connection.commit()

    updated_essay = connection.execute(
        "SELECT id, title, content, font_size, font_style, author, created_at, updated_at FROM Essays WHERE id=?",
        (essay_id,),
    ).fetchone()

    return {
        "ok": True,
        "essay": {
            "id": updated_essay[0],
            "title": updated_essay[1],
            "content": updated_essay[2],
            "font_size": updated_essay[3],
            "font_style": updated_essay[4],
            "author": updated_essay[5],
            "created_at": updated_essay[6],
            "updated_at": updated_essay[7],
        },
    }


@app.delete("/api/essays/{essay_id}")
def delete_essay(essay_id: int, token: str = None, authorization: str = Header(None)):
    if authorization and authorization.lower().startswith("bearer "):
        token = authorization.split(" ", 1)[1]

    username = None
    if token:
        result = connection.execute(
            "SELECT username FROM Sessions WHERE token=?", (token,)
        ).fetchone()
        if result:
            username = result[0]

    if not username:
        raise HTTPException(status_code=401, detail="Unauthorized")

    essay_data = connection.execute(
        "SELECT author FROM Essays WHERE id=?", (essay_id,)
    ).fetchone()

    if not essay_data:
        raise HTTPException(status_code=404, detail="Essay not found")
    if essay_data[0] != username:
        raise HTTPException(status_code=403, detail="Forbidden")

    connection.execute("DELETE FROM Essays WHERE id=?", (essay_id,))
    connection.commit()

    return {"ok": True}


# ============ BLOOM FILTER STATS ============
@app.get("/api/bloom-filter/stats")
async def get_bloom_stats(token: str = None, authorization: str = Header(None)):
    """Returnează statistici despre Bloom Filter."""
    if authorization and authorization.lower().startswith("bearer "):
        token = authorization.split(" ", 1)[1]

    authenticated = False
    if token:
        result = connection.execute(
            "SELECT username FROM Sessions WHERE token=?", (token,)
        ).fetchone()
        authenticated = result is not None

    return {"stats": username_checker.get_stats(), "authenticated": authenticated}


@app.get("/api/health")
def health_check():
    """Verifică starea API-ului."""
    # Simple health endpoint; extend as needed with deeper checks
    return {"status": "ok"}


# ============ SPELLCHECK ============
@app.post("/api/spellcheck")
def api_spellcheck(req: SpellCheckRequest):
    """Check words validity. Returns array of {value, normalize, valid}."""

    def normalize_word(w: str) -> str:
        # Keep alphanumeric unicode chars only, lowercase
        return "".join(ch for ch in w if ch.isalnum()).lower()

    # Build list of input words from either text or provided words
    words: List[str] = []
    if req.words is not None:
        words = [w for w in req.words if isinstance(w, str)]
    elif isinstance(req.text, str):
        # split on whitespace; server will normalize further
        words = req.text.split()
    else:
        return {"results": []}

    results: List[dict] = []
    for w in words:
        norm = normalize_word(w)
        if not norm:
            continue
        is_valid = spell_check_word(norm)
        if len(norm) == 1:
            is_valid = True
        results.append({
            "value": w,
            "normalize": norm,
            "valid": bool(is_valid),
        })

    return {"results": results}


@app.post("/api/signup")
def signup(request: SignupRequest):
    nick = request.nickname.strip()
    if not nick:
        return JSONResponse(status_code=400, content={"error": "nick required"})

    if username_checker.check(request.nickname):
        return JSONResponse(status_code=409, content={"error": "username_exists"})

    password = request.password
    if passcheck.check(password):
        return JSONResponse(status_code=409, content={"error": "password_is_vulnerable"})

    token = secrets.token_urlsafe(32)

    connection.execute(
        "INSERT INTO Users(username, password) VALUES(?,?)",
        (request.nickname, pbkdf2_sha256.hash(password)),
    )
    connection.execute("INSERT INTO Sessions(token, username) VALUES(?,?)", (token, nick))
    connection.commit()

    username_checker.add(request.nickname)

    return {"ok": True, "nickname": nick, "password": password, "token": token}
