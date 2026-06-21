"""
Integration test script for verifying the ScruCheck AI external examiner viewer flow.
"""
import requests
import json
import time

BASE_URL = "http://127.0.0.1:8000"

def run_verification():
    print("=" * 60)
    print("🚀 STARTING EXTERNAL EXAMINER FLOW VERIFICATION")
    print("=" * 60)

    # 1. Login as admin (COE)
    print("\n🔑 1. Logging in as admin...")
    login_resp = requests.post(f"{BASE_URL}/api/auth/login", json={
        "username": "admin",
        "password": "admin123"
    })
    if login_resp.status_code != 200:
        print(f"❌ Login failed: {login_resp.text}")
        return False
    
    admin_token = login_resp.json()["access_token"]
    print("✅ Admin login successful.")

    # 2. Run analysis to populate RESULTS_STORE
    print("\n🔬 2. Running question paper analysis...")
    files = {
        'question_paper': ('sample_question_paper.docx', open('samples/sample_question_paper.docx', 'rb'), 'application/octet-stream'),
        'syllabus': ('sample_syllabus.docx', open('samples/sample_syllabus.docx', 'rb'), 'application/octet-stream'),
    }
    analyze_resp = requests.post(f"{BASE_URL}/api/analyze", files=files)
    if analyze_resp.status_code != 200:
        print(f"❌ Analysis failed: {analyze_resp.text}")
        return False
        
    paper_id = analyze_resp.json()["paper_id"]
    print(f"✅ Analysis completed. Paper ID: {paper_id}")

    # 3. Generate external access link scoped to this paper_id
    print(f"\n🔗 3. Generating external link for paper: {paper_id}...")
    headers = {"Authorization": f"Bearer {admin_token}"}
    generate_resp = requests.post(
        f"{BASE_URL}/api/external/generate",
        json={"paper_ids": [paper_id], "expires_hours": 2},
        headers=headers
    )
    if generate_resp.status_code != 200:
        print(f"❌ External link generation failed: {generate_resp.text}")
        return False
        
    token = generate_resp.json()["token"]
    access_url = generate_resp.json()["access_url"]
    print(f"✅ External link generated successfully. Token: {token}")
    print(f"   Access URL: {access_url}")

    # 4. View papers using external token (as external examiner, no headers)
    print("\n🛡️ 4. Attempting to view results as external examiner (no auth)...")
    view_resp = requests.get(f"{BASE_URL}/api/external/view/{token}")
    if view_resp.status_code != 200:
        print(f"❌ External view failed: {view_resp.text}")
        return False
        
    view_data = view_resp.json()
    print("✅ External view call returned 200 OK.")
    
    # Verify paper is in the results
    if paper_id in view_data["results"]:
        result_payload = view_data["results"][paper_id]
        print(f"🎉 SUCCESS: Found analysis results for {paper_id} inside token view response!")
        print(f"   Score: {result_payload['score']}")
        print(f"   Overall Status: {result_payload['overall_status']}")
        print(f"   Findings (criteria): {len(result_payload['findings'])}")
        print(f"   Bloom's Taxonomy levels: {list(result_payload['blooms_distribution'].keys())}")
    else:
        print(f"❌ FAIL: Scoped paper {paper_id} not found in the external view results.")
        return False

    # 5. Revoke external access link
    print(f"\n🚫 5. Revoking external link token: {token}...")
    revoke_resp = requests.delete(f"{BASE_URL}/api/external/revoke/{token}", headers=headers)
    if revoke_resp.status_code != 200:
        print(f"❌ Revocation failed: {revoke_resp.text}")
        return False
    print("✅ External link token revoked.")

    # 6. Try viewing again to verify invalidation
    print("\n🔍 6. Attempting to view results again after revocation...")
    view_revoked_resp = requests.get(f"{BASE_URL}/api/external/view/{token}")
    if view_revoked_resp.status_code == 401:
        print("🎉 SUCCESS: Revoked link returned 401 Unauthorized as expected!")
    else:
        print(f"❌ FAIL: Revoked link returned status {view_revoked_resp.status_code} instead of 401.")
        return False

    print("\n" + "=" * 60)
    print("🌟 ALL VERIFICATION CHECKS PASSED SUCCESSFULLY!")
    print("=" * 60)
    return True

if __name__ == "__main__":
    run_verification()
