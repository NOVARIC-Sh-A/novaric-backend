from dotenv import load_dotenv
import os

load_dotenv()

print("URL:", os.environ.get("SUPABASE_URL"))
print("KEY:", os.environ.get("SUPABASE_SERVICE_ROLE_KEY")[:12] + "...")
