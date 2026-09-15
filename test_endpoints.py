import urllib.request
import urllib.parse
import json

BASE = "http://127.0.0.1:8000"

def post(url, data, token=None):
    req = urllib.request.Request(BASE + url, data=json.dumps(data).encode('utf-8'), headers={'Content-Type': 'application/json'})
    if token:
        req.add_header('Authorization', f'Bearer {token}')
    try:
        with urllib.request.urlopen(req) as resp:
            return resp.status, json.loads(resp.read().decode('utf-8'))
    except urllib.error.HTTPError as e:
        return e.code, e.read().decode('utf-8')

def get(url, token=None):
    req = urllib.request.Request(BASE + url)
    if token:
        req.add_header('Authorization', f'Bearer {token}')
    try:
        with urllib.request.urlopen(req) as resp:
            return resp.status, json.loads(resp.read().decode('utf-8'))
    except urllib.error.HTTPError as e:
        return e.code, e.read().decode('utf-8')

print("1. Testing Health...")
status, body = get("/health")
print("Health:", status, body)

print("\n2. Testing Nurse Login...")
status, body = post("/auth/login", {"email": "nurse.sunita@clinassistai.com", "password": "Nurse@123"})
print("Nurse login status:", status)
nurse_token = body.get("access_token")

print("\n3. Testing Doctor Login...")
status, body = post("/auth/login", {"email": "siddharth.varma@clinassistai.com", "password": "Doctor@123"})
print("Doctor login status:", status)
doc_token = body.get("access_token")

print("\n4. Testing Patient Login...")
status, body = post("/auth/login", {"email": "ramesh.patel@example.com", "password": "Patient@123"})
print("Patient login status:", status)
pat_token = body.get("access_token")

print("\n5. Testing Assistant Endpoints...")
status, body = get("/assistant/stats", nurse_token)
print("Assistant stats:", status, body)

status, body = get("/assistant/doctors", nurse_token)
print("Assistant doctors:", status, f"{len(body)} doctors" if status == 200 else body)

status, body = get("/assistant/recent-triages", nurse_token)
print("Assistant recent triages:", status, f"{len(body)} triages" if status == 200 else body)

print("\n6. Testing Doctor Endpoints...")
status, body = get("/doctor/patients", doc_token)
print("Doctor patients:", status, f"{len(body)} patients" if status == 200 else body)
if status == 200 and body:
    pid = body[0]["patient_id"]
    sid = body[0]["session_id"]
    print(f"Testing doctor patient detail for {pid}...")
    d_status, d_body = get(f"/doctor/patient/{pid}", doc_token)
    print("Doctor patient detail:", d_status)
    if d_status != 200:
        print("ERROR in doctor patient detail:", d_body)
    
    print(f"Testing FHIR bundle for {pid}...")
    f_status, f_body = get(f"/ai/fhir/{pid}", doc_token)
    print("FHIR status:", f_status)

print("\n7. Testing Patient Endpoints...")
status, body = get("/patients/me", pat_token)
print("Patient me:", status)
status, body = get("/patients/me/sessions", pat_token)
print("Patient sessions:", status, f"{len(body)} sessions" if status == 200 else body)

print("\nALL ENDPOINT TESTS COMPLETE!")
