import urllib.request
import json
import time

try:
    print("Fetching /openapi.json...")
    req = urllib.request.Request("http://127.0.0.1:8001/openapi.json")
    with urllib.request.urlopen(req) as res:
        if res.status == 200:
            data = json.loads(res.read().decode())
            print("Success! OpenAPI loaded.")
            mentoring_paths = [p for p in data["paths"] if "mentoring" in p]
            print(f"Found {len(mentoring_paths)} mentoring endpoints:")
            for p in mentoring_paths:
                print(" -", p)
        else:
            print("Failed to load openapi:", res.status)
except Exception as e:
    print("Error:", e)
