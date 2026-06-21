import requests

payload = {
    "question": "Define Ohm's Law.",
    "issue_type": "bloom_level",
    "current_finding": "Question is at Remember level. Low cognitive demand.",
    "current_bloom_level": "Remember",
    "target_bloom_level": "Analyze"
}

r = requests.post("http://127.0.0.1:8000/api/improve", json=payload, timeout=30)
print("Status:", r.status_code)
if r.status_code == 200:
    d = r.json()
    print("Original :", d["original_question"])
    print("Improved :", d["improved_question"])
    print("Changes  :", d["changes_made"])
    print("Reasoning:", d["reasoning"])
else:
    print("Error:", r.text[:300])
