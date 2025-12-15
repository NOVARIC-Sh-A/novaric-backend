import requests
import json
import sys

API_BASE_URL = "https://novaric-backend-386598211704.europe-west1.run.app"
# For local testing:
# API_BASE_URL = "http://localhost:8080"

def test_recompute(politician_id: int):
    url = f"{API_BASE_URL}/api/paragon/recompute/{politician_id}"

    print(f"\n🔵 Testing PARAGON recompute for ID: {politician_id}")
    print(f"   → {url}\n")

    try:
        response = requests.post(url, timeout=120)

        print(f"Status Code: {response.status_code}")

        if response.status_code != 200:
            print("❌ ERROR:", response.text)
            return

        print("✔ PARAGON recompute successful\n")

        data = response.json()
        print(json.dumps(data, indent=4, ensure_ascii=False))

        print("\n🔍 Sanity Checks:")
        print(" - overall_score:", data.get("overall_score"))
        print(" - dimensions:", len(data.get("dimensions", [])))
        print(" - snapshot.calculated_at:", data.get("snapshot", {}).get("calculated_at"))
        print(" - metrics keys:", list(data.get("metrics", {}).keys())[:10])

        if "dimensions_json" in data.get("snapshot", {}):
            print(" - dimensions_json: ✔ present")
        else:
            print(" - dimensions_json: ✘ missing")

    except Exception as e:
        print("❌ Exception raised:")
        print(e)

if __name__ == "__main__":
    pid = int(sys.argv[1]) if len(sys.argv) > 1 else 1
    test_recompute(pid)
