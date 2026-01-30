import { createClient } from '@supabase/supabase-js';

const SUPABASE_URL = 'https://xhryczkrddsawksqxgrx.supabase.co'; // your project URL
const SUPABASE_PUBLISHABLE_KEY = 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InhocnljemtyZGRzYXdrc3F4Z3J4Iiwicm9sZSI6ImFub24iLCJpYXQiOjE3NTEwNDE4MTksImV4cCI6MjA2NjYxNzgxOX0.XIV65Ubd0tF0sfIVXQZPJjIkINmLqvHwVJ9ofWDZJHw'; // your anon/public key

export const supabase = createClient(SUPABASE_URL, SUPABASE_PUBLISHABLE_KEY);
