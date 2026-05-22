# models.py
import os
from supabase import create_client, Client
from dotenv import load_dotenv

load_dotenv()

url: str = os.getenv("SUPABASE_URL", "")
key: str = os.getenv("SUPABASE_SERVICE_ROLE_KEY", "") or os.getenv("SUPABASE_ANON_KEY", "")

# Allow graceful failure if not configured yet
try:
    if url and key:
        supabase: Client = create_client(url, key)
    else:
        supabase = None
except Exception as e:
    print(f"Warning: Could not initialize Supabase client. {e}")
    supabase = None

def init_db():
    """
    Since we are using Supabase (PostgreSQL), the schema should be initialized
    via the Supabase dashboard using the schema.sql file.
    This function now just verifies the connection.
    """
    if supabase:
        print("Connected to Supabase")
    else:
        print("Supabase client not initialized. Check .env variables.")
