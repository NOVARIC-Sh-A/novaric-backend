import os
from dataclasses import dataclass


@dataclass(frozen=True)
class SupabaseEnv:
    url: str | None
    publishable_key: str | None
    secret_key: str | None


def load_supabase_env() -> SupabaseEnv:
    url = os.getenv("SUPABASE_URL") or os.getenv("SUPABASE_PROJECT_URL")

    publishable_key = (
        os.getenv("SUPABASE_ANON_KEY")
        or os.getenv("SUPABASE_ANON_KEY")  # legacy fallback
    )

    secret_key = (
        os.getenv("SUPABASE_SERVICE_ROLE_KEY")
        or os.getenv("SUPABASE_SERVICE_ROLE_KEY")  # legacy fallback
    )

    return SupabaseEnv(url=url, publishable_key=publishable_key, secret_key=secret_key)
