from fastapi.testclient import TestClient
from main import app


def test_upload_and_search():
    client = TestClient(app)

    # Login using demo credentials
    resp = client.post('/api/auth/login', json={'username': 'demo', 'password': 'demo123'})
    assert resp.status_code == 200
    token = resp.json().get('token')
    assert token

    headers = {'Authorization': f'Bearer {token}'}

    # Upload a small text file
    files = {'file': ('sample.txt', b'Hello wonderful world\nThis is a sample document with quote segments', 'text/plain')}
    data = {'title': 'TestUpload'}
    resp = client.post('/api/books/upload', headers=headers, data=data, files=files)
    assert resp.status_code == 200

    # Now search for a short quote that should be present
    search_payload = {'quote': 'wonderful world'}
    resp = client.post('/api/quotes/search', headers=headers, json=search_payload)
    assert resp.status_code == 200
    body = resp.json()
    assert body.get('found') is True
    sources = body.get('sources') or []
    # ensure at least one of the returned occurrences refers to TestUpload
    titles = [s.get('title') for s in sources if isinstance(s, dict)]
    assert 'TestUpload' in titles
    # check snippet & page/paragraph info for uploaded book
    for s in sources:
        if s.get('title') == 'TestUpload':
            assert s.get('snippet') is not None
            assert s.get('page') is not None
            assert s.get('paragraph') is not None
            break


def test_docx_upload_and_search():
    try:
        from docx import Document as Dox
        from io import BytesIO
    except Exception:
        # python-docx not installed in environment - skip this test
        return

    client = TestClient(app)
    resp = client.post('/api/auth/login', json={'username': 'demo', 'password': 'demo123'})
    token = resp.json().get('token')
    headers = {'Authorization': f'Bearer {token}'}

    doc = Dox()
    doc.add_paragraph('This is a minimal docx containing the phrase wonderful world for testing')
    bio = BytesIO()
    doc.save(bio)
    bio.seek(0)

    files = {'file': ('sample.docx', bio.read(), 'application/vnd.openxmlformats-officedocument.wordprocessingml.document')}
    data = {'title': 'DocxUpload'}
    resp = client.post('/api/books/upload', headers=headers, data=data, files=files)
    assert resp.status_code == 200

    resp = client.post('/api/quotes/search', headers=headers, json={'quote': 'wonderful world'})
    assert resp.status_code == 200
    body = resp.json()
    assert body.get('found') is True
    titles = [s.get('title') for s in (body.get('sources') or []) if isinstance(s, dict)]
    assert 'DocxUpload' in titles
    # multiple occurrences may be returned per book; ensure snippet/page/paragraph present
    for s in (body.get('sources') or []):
        if s.get('title') == 'DocxUpload':
            assert 'snippet' in s
            assert 'page' in s
            assert 'paragraph' in s
            break


def test_public_search_without_auth():
    client = TestClient(app)
    # We will search for the phrase uploaded in test_upload_and_search without providing token
    resp = client.post('/api/quotes/search', json={'quote': 'wonderful world'})
    assert resp.status_code == 200
    body = resp.json()
    assert body.get('found') is True
    assert 'TestUpload' in [s.get('title') for s in (body.get('sources') or []) if isinstance(s, dict)]
