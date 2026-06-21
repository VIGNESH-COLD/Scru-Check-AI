"""
Test script for ScruCheck AI API
"""
import requests
import json

BASE_URL = "http://127.0.0.1:8000"

def test_login():
    print("=" * 50)
    print("Testing Login API")
    print("=" * 50)
    
    # Test admin login
    r = requests.post(f"{BASE_URL}/api/auth/login", json={
        "username": "admin", 
        "password": "admin123"
    })
    
    print(f"Status: {r.status_code}")
    
    if r.status_code == 200:
        data = r.json()
        print(f"User: {data['user']['username']}")
        print(f"Role: {data['user']['role']}")
        print(f"Permissions: {len(data['user']['permissions'])} permissions")
        print(f"Token: {data['access_token'][:50]}...")
        return data['access_token']
    else:
        print(f"Error: {r.text}")
        return None

def test_analysis():
    print("\n" + "=" * 50)
    print("Testing Analysis API")
    print("=" * 50)
    
    files = {
        'question_paper': ('sample_question_paper.docx', open('samples/sample_question_paper.docx', 'rb'), 'application/octet-stream'),
        'syllabus': ('sample_syllabus.docx', open('samples/sample_syllabus.docx', 'rb'), 'application/octet-stream'),
    }
    
    r = requests.post(f"{BASE_URL}/api/analyze", files=files)
    
    print(f"Status: {r.status_code}")
    
    if r.status_code == 200:
        data = r.json()
        print(f"Paper ID: {data['paper_id']}")
        print(f"Overall Status: {data['overall_status']}")
        print(f"Blooms Distribution: {data['blooms_distribution']}")
        print(f"Syllabus Coverage: {data['syllabus_coverage']}")
        print(f"CO Mapping Count: {len(data['co_mapping'])}")
        return data['paper_id']
    else:
        print(f"Error: {r.text[:200]}")
        return None

def test_external_access(token):
    print("\n" + "=" * 50)
    print("Testing External Access API")
    print("=" * 50)
    
    headers = {"Authorization": f"Bearer {token}"}
    
    r = requests.post(
        f"{BASE_URL}/api/external/generate",
        json={"paper_ids": ["test-paper-1"], "expires_hours": 24},
        headers=headers
    )
    
    print(f"Generate Link Status: {r.status_code}")
    
    if r.status_code == 200:
        data = r.json()
        print(f"Access URL: {data['access_url']}")
        print(f"Expires: {data['expires_at']}")
        return data['token']
    else:
        print(f"Error: {r.text}")
        return None

if __name__ == "__main__":
    print("ScruCheck AI API Test Suite")
    print("=" * 50)
    
    # Test login
    token = test_login()
    
    # Test analysis
    if token:
        paper_id = test_analysis()
    
    # Test external access
    if token:
        ext_token = test_external_access(token)
    
    print("\n" + "=" * 50)
    print("All tests completed!")
    print("=" * 50)
