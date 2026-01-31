export const SUPABASE_URL =
    process.env.SUPABASE_URL || process.env.SUPABASE_PROJECT_URL;

export const SUPABASE_ANON_KEY =
    process.env.SUPABASE_ANON_KEY || process.env.SUPABASE_ANON_KEY;

export const SUPABASE_SERVICE_ROLE_KEY =
    process.env.SUPABASE_SERVICE_ROLE_KEY || process.env.SUPABASE_SERVICE_ROLE_KEY;

// For legacy code paths expecting a generic key:
export const SUPABASE_KEY =
    process.env.SUPABASE_KEY || SUPABASE_SERVICE_ROLE_KEY || SUPABASE_ANON_KEY;

if (!SUPABASE_URL || !SUPABASE_KEY) {
    throw new Error("SUPABASE_URL or SUPABASE_KEY missing/invalid");
}
