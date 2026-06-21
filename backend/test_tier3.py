"""
Comprehensive Tier 3 Feature Verification Test
Tests RBAC, JWT Auth, External Portal, and Audit Logging
"""
import requests
import json
import time

BASE_URL = "http://127.0.0.1:8000"

# Test results
results = {
    "passed": 0,
    "failed": 0,
    "tests": []
}

def test(name, condition, details=""):
    if condition:
        results["passed"] += 1
        results["tests"].append({"name": name, "status": "PASS", "details": details})
        print(f"  ✅ {name}")
    else:
        results["failed"] += 1
        results["tests"].append({"name": name, "status": "FAIL", "details": details})
        print(f"  ❌ {name} - {details}")


print("=" * 60)
print("TIER 3 FEATURE VERIFICATION TEST")
print("=" * 60)

# =============================================
# 1. JWT AUTHENTICATION TESTS
# =============================================
print("\n📋 1. JWT AUTHENTICATION")
print("-" * 40)

# Test 1.1: Login with valid credentials
try:
    r = requests.post(f"{BASE_URL}/api/auth/login", json={
        "username": "admin",
        "password": "admin123"
    }, timeout=10)
    admin_token = r.json().get("access_token") if r.status_code == 200 else None
    test("Admin login", r.status_code == 200 and admin_token is not None, f"Status: {r.status_code}")
except Exception as e:
    test("Admin login", False, str(e))
    admin_token = None

# Test 1.2: Login with invalid credentials
try:
    r = requests.post(f"{BASE_URL}/api/auth/login", json={
        "username": "admin",
        "password": "wrongpassword"
    }, timeout=10)
    test("Invalid login rejected", r.status_code == 401, f"Status: {r.status_code}")
except Exception as e:
    test("Invalid login rejected", False, str(e))

# Test 1.3: Get current user info
try:
    r = requests.get(f"{BASE_URL}/api/auth/me", 
                     headers={"Authorization": f"Bearer {admin_token}"}, timeout=10)
    test("Get current user", r.status_code == 200, f"Status: {r.status_code}")
except Exception as e:
    test("Get current user", False, str(e))

# Test 1.4: Faculty login
try:
    r = requests.post(f"{BASE_URL}/api/auth/login", json={
        "username": "faculty_demo",
        "password": "faculty123"
    }, timeout=10)
    faculty_token = r.json().get("access_token") if r.status_code == 200 else None
    test("Faculty login", r.status_code == 200 and faculty_token is not None, f"Status: {r.status_code}")
except Exception as e:
    test("Faculty login", False, str(e))
    faculty_token = None

# Test 1.5: HOD login
try:
    r = requests.post(f"{BASE_URL}/api/auth/login", json={
        "username": "hod_demo",
        "password": "hod123"
    }, timeout=10)
    hod_token = r.json().get("access_token") if r.status_code == 200 else None
    test("HOD login", r.status_code == 200 and hod_token is not None, f"Status: {r.status_code}")
except Exception as e:
    test("HOD login", False, str(e))
    hod_token = None


# =============================================
# 2. RBAC (ROLE-BASED ACCESS CONTROL) TESTS
# =============================================
print("\n📋 2. RBAC (ROLE-BASED ACCESS CONTROL)")
print("-" * 40)

# Test 2.1: COE can list all users
try:
    r = requests.get(f"{BASE_URL}/api/auth/users", 
                     headers={"Authorization": f"Bearer {admin_token}"}, timeout=10)
    users = r.json() if r.status_code == 200 else []
    test("COE can list users", r.status_code == 200 and len(users) > 0, f"Found {len(users)} users")
except Exception as e:
    test("COE can list users", False, str(e))

# Test 2.2: Faculty cannot list users (should return empty or forbidden)
try:
    r = requests.get(f"{BASE_URL}/api/auth/users", 
                     headers={"Authorization": f"Bearer {faculty_token}"}, timeout=10)
    users = r.json() if r.status_code == 200 else []
    # Faculty should get empty list or 403
    test("Faculty user list restricted", 
         (r.status_code == 200 and len(users) == 0) or (r.status_code == 403), 
         f"Status: {r.status_code}, Users: {len(users) if r.status_code == 200 else 'N/A'}")
except Exception as e:
    test("Faculty user list restricted", False, str(e))

# Test 2.3: Check role permissions in token
try:
    r = requests.get(f"{BASE_URL}/api/auth/me", 
                     headers={"Authorization": f"Bearer {admin_token}"}, timeout=10)
    data = r.json() if r.status_code == 200 else {}
    permissions = data.get("permissions", [])
    has_manage = "manage_users" in permissions
    test("COE has manage_users permission", has_manage, f"{len(permissions)} permissions found")
except Exception as e:
    test("COE has manage_users permission", False, str(e))

# Test 2.4: Faculty does not have manage_users permission
try:
    r = requests.get(f"{BASE_URL}/api/auth/me", 
                     headers={"Authorization": f"Bearer {faculty_token}"}, timeout=10)
    data = r.json() if r.status_code == 200 else {}
    permissions = data.get("permissions", [])
    no_manage = "manage_users" not in permissions
    test("Faculty lacks manage_users", no_manage, f"Permissions: {permissions}")
except Exception as e:
    test("Faculty lacks manage_users", False, str(e))


# =============================================
# 3. EXTERNAL EXAMINER PORTAL TESTS
# =============================================
print("\n📋 3. EXTERNAL EXAMINER PORTAL")
print("-" * 40)

ext_token = None

# Test 3.1: HOD can generate external link
try:
    r = requests.post(f"{BASE_URL}/api/external/generate", 
                      headers={"Authorization": f"Bearer {hod_token}"},
                      json={"paper_ids": ["test-paper-1"], "expires_hours": 24},
                      timeout=10)
    if r.status_code == 200:
        ext_token = r.json().get("token")
    test("HOD can generate external link", r.status_code == 200 and ext_token is not None, 
         f"Status: {r.status_code}")
except Exception as e:
    test("HOD can generate external link", False, str(e))

# Test 3.2: Faculty cannot generate external link
try:
    r = requests.post(f"{BASE_URL}/api/external/generate", 
                      headers={"Authorization": f"Bearer {faculty_token}"},
                      json={"paper_ids": ["test-paper-2"], "expires_hours": 24},
                      timeout=10)
    test("Faculty cannot generate link", r.status_code == 403, f"Status: {r.status_code}")
except Exception as e:
    test("Faculty cannot generate link", False, str(e))

# Test 3.3: Verify external token
if ext_token:
    try:
        r = requests.get(f"{BASE_URL}/api/external/verify/{ext_token}", timeout=10)
        test("Verify external token", r.status_code == 200, f"Status: {r.status_code}")
    except Exception as e:
        test("Verify external token", False, str(e))
else:
    test("Verify external token", False, "No token generated")

# Test 3.4: View papers with external token
if ext_token:
    try:
        r = requests.get(f"{BASE_URL}/api/external/view/{ext_token}", timeout=10)
        test("View papers with token", r.status_code == 200, f"Status: {r.status_code}")
    except Exception as e:
        test("View papers with token", False, str(e))
else:
    test("View papers with token", False, "No token generated")

# Test 3.5: List active tokens
try:
    r = requests.get(f"{BASE_URL}/api/external/tokens", 
                     headers={"Authorization": f"Bearer {admin_token}"}, timeout=10)
    test("List active tokens", r.status_code == 200, f"Status: {r.status_code}")
except Exception as e:
    test("List active tokens", False, str(e))


# =============================================
# 4. AUDIT LOGGING TESTS
# =============================================
print("\n📋 4. AUDIT LOGGING")
print("-" * 40)

# Test 4.1: Check audit log file exists
import os
audit_file = "audit_log.jsonl"
test("Audit log file exists", os.path.exists(audit_file), f"Path: {audit_file}")

# Test 4.2: Check audit log has entries
if os.path.exists(audit_file):
    try:
        with open(audit_file, 'r') as f:
            lines = f.readlines()
        test("Audit log has entries", len(lines) > 0, f"{len(lines)} entries")
    except Exception as e:
        test("Audit log has entries", False, str(e))
else:
    test("Audit log has entries", False, "File not found")

# Test 4.3: Check login events are logged
if os.path.exists(audit_file):
    try:
        with open(audit_file, 'r') as f:
            content = f.read()
        has_login = "LOGIN" in content
        test("Login events logged", has_login, "Found LOGIN entries" if has_login else "No LOGIN entries")
    except Exception as e:
        test("Login events logged", False, str(e))
else:
    test("Login events logged", False, "File not found")


# =============================================
# 5. FRONTEND AUTH COMPONENTS
# =============================================
print("\n📋 5. FRONTEND AUTH COMPONENTS")
print("-" * 40)

# Test 5.1: Check AuthContext.jsx exists
auth_context = "../frontend/src/context/AuthContext.jsx"
test("AuthContext.jsx exists", os.path.exists(auth_context), f"Path: {auth_context}")

# Test 5.2: Check Login.jsx exists
login_component = "../frontend/src/components/Login.jsx"
test("Login.jsx exists", os.path.exists(login_component), f"Path: {login_component}")

# Test 5.3: Check AdminPanel.jsx exists
admin_panel = "../frontend/src/components/AdminPanel.jsx"
test("AdminPanel.jsx exists", os.path.exists(admin_panel), f"Path: {admin_panel}")

# Test 5.4: Check Header has auth integration
header_file = "../frontend/src/components/Header.jsx"
if os.path.exists(header_file):
    with open(header_file, 'r') as f:
        content = f.read()
    has_auth = "useAuth" in content
    test("Header has auth integration", has_auth, "useAuth imported" if has_auth else "No auth import")
else:
    test("Header has auth integration", False, "File not found")


# =============================================
# SUMMARY
# =============================================
print("\n" + "=" * 60)
print("TEST SUMMARY")
print("=" * 60)
print(f"✅ Passed: {results['passed']}")
print(f"❌ Failed: {results['failed']}")
print(f"📊 Total:  {results['passed'] + results['failed']}")
print(f"📈 Score:  {results['passed'] / (results['passed'] + results['failed']) * 100:.1f}%")
print("=" * 60)

if results['failed'] > 0:
    print("\nFailed Tests:")
    for t in results['tests']:
        if t['status'] == 'FAIL':
            print(f"  - {t['name']}: {t['details']}")
