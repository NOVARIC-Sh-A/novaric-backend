# tools/export_politicians.py
import json
from mock_profiles import mock_political_profiles_data  # reuse existing list

def to_slug(name: str) -> str:
    return (
        name.lower()
        .replace("ë", "e")
        .replace("ç", "c")
        .replace(" ", "-")
        .replace("(", "")
        .replace(")", "")
    )

def export():
    politicians = []
    for profile in mock_political_profiles_data:
        politicians.append({
            "legacy_id": profile.get("id"),
            "full_name": profile["name"],
            "slug": to_slug(profile["name"]),
            "party": (profile.get("category") or "").replace("Politikë", "").strip(" ()"),
            "role": "Deputet" if profile.get("category", "").startswith("Politikë") else None,
            "photo_url": profile.get("imageUrl"),
        })
    with open("politicians.json", "w", encoding="utf-8") as f:
        json.dump(politicians, f, ensure_ascii=False, indent=2)

if __name__ == "__main__":
    export()
