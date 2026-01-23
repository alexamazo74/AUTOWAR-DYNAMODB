import sys
import os
sys.path.insert(0, os.path.abspath('src'))
from fastapi.testclient import TestClient
from app.main import app
from app.cognito_auth import require_cognito_auth

# Bypass cognito auth for tests
app.dependency_overrides[require_cognito_auth] = lambda: {'sub': 'test-user'}

client = TestClient(app)

payload = {
    'evaluation_id': 'test-eval-1',
    'bp_id': 'bp-001',
    'scores': {
        's1': 3,
        's2': 4.5,
        's3': 2
    }
}

print('POST /scores')
r = client.post('/scores', json=payload)
print(r.status_code)
print(r.json())

if r.status_code == 201:
    item = r.json()
    sid = item.get('id')
    print('\nGET /scores/{id}')
    r2 = client.get(f"/scores/{sid}")
    print(r2.status_code)
    print(r2.json())

    print('\nGET /evaluations/test-eval-1/scores')
    r3 = client.get('/evaluations/test-eval-1/scores')
    print(r3.status_code)
    print(r3.json())
