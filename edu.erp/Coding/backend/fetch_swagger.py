import requests
import json
import os

def fetch_swagger(output_path: str = "openapi.json"):
    """Fetch the OpenAPI spec from the running FastAPI server and save it to a file.

    By default it contacts http://127.0.0.1:8000/openapi.json
    """
    url = "http://127.0.0.1:8000/openapi.json"
    try:
        response = requests.get(url)
        response.raise_for_status()
        data = response.json()
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2)
        print(f"OpenAPI spec saved to {output_path}")
    except Exception as e:
        print(f"Failed to fetch OpenAPI spec: {e}")

if __name__ == "__main__":
    fetch_swagger()
