import json
import os

def load_metrics():
    """
    Loads the politician_metrics.json file from the data directory.
    Returns an empty dict if file not found.
    """
    # Build path relative to this file to ensure it works regardless of where main.py is run
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    file_path = os.path.join(base_dir, "data", "politician_metrics.json")
    
    try:
        with open(file_path, "r", encoding="utf-8") as file:
            return json.load(file)
    except FileNotFoundError:
        print(f"⚠️ Warning: Metrics file not found at {file_path}. Using fallback scores.")
        return {}
    except json.JSONDecodeError:
        print(f"⚠️ Error: Failed to decode JSON from {file_path}.")
        return {}
