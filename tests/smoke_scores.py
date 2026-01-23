import sys
import os
sys.path.insert(0, os.path.abspath('src'))
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)
resp = client.get('/evaluations/test-eval-1/scores')
print(resp.status_code)
print(resp.json())
