from fastapi.testclient import TestClient
from main import app
from datetime import datetime


def test_essays_crud():
    c = TestClient(app)
    # login
    resp = c.post('/api/auth/login', json={'username': 'demo', 'password': 'demo123'})
    assert resp.status_code == 200
    token = resp.json().get('token')
    headers = {'Authorization': f'Bearer {token}'}

    # create essay
    create_resp = c.post('/api/essays', headers=headers, json={'title': 'My Essay', 'content': 'This is a test', 'font_size': 14, 'font_style': 'Arial'})
    assert create_resp.status_code == 200
    eid = create_resp.json()['essay_id']

    # get essay
    get_resp = c.get(f'/api/essays/{eid}', headers=headers)
    assert get_resp.status_code == 200
    assert get_resp.json()['essay']['title'] == 'My Essay'

    # update essay
    upd_resp = c.put(f'/api/essays/{eid}', headers=headers, json={'title': 'My Essay Updated', 'content': 'Updated', 'font_size': 12, 'font_style': 'Times'})
    assert upd_resp.status_code == 200
    assert upd_resp.json()['essay']['title'] == 'My Essay Updated'

    # list essays
    list_resp = c.get('/api/essays', headers=headers)
    assert list_resp.status_code == 200
    assert any(e['id'] == eid for e in list_resp.json()['essays'])

    # delete
    del_resp = c.delete(f'/api/essays/{eid}', headers=headers)
    assert del_resp.status_code == 200
    # ensure deleted
    get_resp2 = c.get(f'/api/essays/{eid}', headers=headers)
    assert get_resp2.status_code == 404
