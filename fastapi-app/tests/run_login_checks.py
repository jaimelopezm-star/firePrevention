import os
import sys
from fastapi.testclient import TestClient

# Ensure project root is on sys.path so imports like `import main` work
ROOT = os.path.dirname(os.path.dirname(__file__))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

from main import app

client = TestClient(app)

endpoints = [
    ("/api/v1/auth/login/admin", {"email": "master@fire.com", "password": "master123"}),
    ("/api/v1/auth/login/user", {"email": "usuario@fire.com", "password": "usuario123"}),
    ("/api/v1/auth/login/manager", {"email": "gerente@fire.com", "password": "gerente123"}),
]

for url, payload in endpoints:
    resp = client.post(url, json=payload)
    print(url, resp.status_code)
    try:
        print(resp.json())
    except Exception as e:
        print("No JSON response", e)
