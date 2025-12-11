import requests
import json
import sys

# ============================================================
# CONFIGURE YOUR BACKEND URL
# ============================================================
API_BASE_URL = "https://novaric-backend-386598211704.europe-west1.run.app"
# Or for local testing:
# API_BASE_URL = "http://localhost:8080"


# ============================================================
# TEST FUNCTION
# ============================================================
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

        # Pretty print JSON
        data = response.json()
        print(json.dumps(data, indent=4, ensure_ascii=False))

        # Sanity checks
        print("\n🔍 Sanity Checks:")
        print(" - overall_score:", data.get("overall_score"))
        print(" - dimensions:", len(data.get("dimensions", [])), "dimensions")
        print(" - snapshot.calculated_at:", data.get("snapshot", {}).get("calculated_at"))
        print(" - metrics:", list(data.get("metrics", {}).keys())[:10], "...")

        if "dimensions_json" in data.get("snapshot", {}):
            print(" - dimensions_json: ✔ present in snapshot")
        else:
            print(" - dimensions_json: ✘ missing")

    except Exception as e:
        print("❌ Exception raised during test:")
        print(e)


# ============================================================
# MAIN
# ============================================================
if __name__ == "__main__":
    if len(sys.argv) > 1:
        pid = int(sys.argv[1])
    else:
        pid = 1  # default test politician

    test_recompute(pid)
