import requests

endpoints = [
    ("/api/v1/auth/login/admin", {"email": "master@fire.com", "password": "master123"}),
    ("/api/v1/auth/login/user", {"email": "usuario@fire.com", "password": "usuario123"}),
    ("/api/v1/auth/login/manager", {"email": "gerente@fire.com", "password": "gerente123"}),
]

base = "http://127.0.0.1:8000"

for path, data in endpoints:
    url = base + path
    r = requests.post(url, json=data)
    print(url, r.status_code)
    try:
        print(r.json())
    except Exception as e:
        print('Raw:', r.text)
