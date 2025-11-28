
# ============ BOOKS ENDPOINTS ============
@app.get("/api/books")
def list_books(token: str = None, authorization: str = Header(None)):
    """Listează toate cărțile încărcate."""
    
    if authorization and authorization.lower().startswith("bearer "):
        token = authorization.split(" ", 1)[1]
        
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
            _ = paragraph

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
    # if authorization and authorization.lower().startswith("bearer "):
    #     token = authorization.split(" ", 1)[1]
    # if not token or token not in sessions:
    #     raise HTTPException(status_code=401, detail="Unauthorized")
    
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
            
        print(text)
        
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
                if bloom_filter.check(s):
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
        if bloom_filter.check(request.quote):
            # Already present; return conflict
            return JSONResponse(status_code=409, content={"error": "duplicate", "message": "Quote already exists"})
        bloom_filter.add(request.quote)
        
        return {
            "success": True,
            "message": f"Citația a fost adăugată din cartea '{request.book_title}'"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/quotes/search")
async def search_quote(request: SearchRequest, token: str = None, authorization: str = Header(None)):
    return {}
    # """Caută o citație în Bloom Filter."""
    # if authorization and authorization.lower().startswith("bearer "):
    #     token = authorization.split(" ", 1)[1]
    # if not token or token not in sessions:
    #     raise HTTPException(status_code=401, detail="Unauthorized")
    
    # if not request.quote.strip():
    #     raise HTTPException(status_code=400, detail="Quote cannot be empty")
    
    # try:
    #     possibly_present = bloom_filter.check(request.quote)
        
    #     if possibly_present:
    #         titles = bloom_filter.get_quote_source(request.quote)
    #         occurrences = []
    #         for title in titles:
    #             bid, book = _find_book_entry_by_title(title)
    #             if book:
    #                 # Return all occurrences for this title
    #                 occs = _extract_all_occurrences(book, request.quote)
    #                 if occs:
    #                     for o in occs:
    #                         occurrences.append({
    #                             'title': title,
    #                             'page': o['page'],
    #                             'paragraph': o['paragraph'],
    #                             'row': o['row'],
    #                             'snippet': o['snippet']
    #                         })
    #                 else:
    #                     occurrences.append({'title': title})
    #             else:
    #                 occurrences.append({'title': title})
    #         return {
    #             "found": True,
    #             "message": "Citația ar putea fi prezentă",
    #             "sources": occurrences if occurrences else ["Posibilă prezență - false positive"],
    #             "authenticated": bool(token and token in sessions)
    #         }
    #     else:
    #         return {
    #             "found": False,
    #             "message": "Citația sigur NU este prezentă în baza de date",
    #             "sources": [],
    #             "authenticated": bool(token and token in sessions)
    #         }
    # except Exception as e:
    #     raise HTTPException(status_code=500, detail=str(e))