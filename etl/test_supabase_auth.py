# etl/test_supabase_auth.py

from utils.supabase_client import _get, SUPABASE_URL, SUPABASE_KEY, is_supabase_configured

def main() -> None:
    print("SUPABASE_URL:", SUPABASE_URL)
    print("configured:", is_supabase_configured())
    print("key_present:", bool(SUPABASE_KEY))
    print("key_type:", "sb_*" if (SUPABASE_KEY or "").startswith("sb_") else "jwt_eyJ_or_other")

    rows = _get("politicians", {"select": "id", "limit": "1"})
    print("politicians sample:", rows)

if __name__ == "__main__":
    main()
