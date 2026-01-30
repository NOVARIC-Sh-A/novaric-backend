from fastapi import APIRouter
from config.supabase_env import load_supabase_env

router = APIRouter()


@router.get("/__supabase")
def supabase_health():
    env = load_supabase_env()

    url_set = bool(env.url)
    publishable_set = bool(env.publishable_key)
    secret_set = bool(env.secret_key)

    if secret_set:
        key_in_use = "secret"
    elif publishable_set:
        key_in_use = "publishable"
    else:
        key_in_use = "none"

    configured = bool(env.url and (env.secret_key or env.publishable_key))

    return {
        "configured": configured,
        "url_set": url_set,
        "url_preview": f"{env.url[:35]}..." if env.url else None,
        "service_role_set": secret_set,
        "anon_set": publishable_set,
        "key_in_use": key_in_use,
        "client_created": configured,
        "client_init_error": None if configured else "SUPABASE_URL or SUPABASE_KEY missing/invalid",
    }
