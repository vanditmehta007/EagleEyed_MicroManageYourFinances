from supabase import create_client, Client
from backend.config import settings

# Initialize Supabase client
# Make sure to set SUPABASE_URL and SUPABASE_KEY in your .env file
url: str = settings.SUPABASE_URL or "https://your-project.supabase.co"
key: str = settings.SUPABASE_KEY or "your-anon-key"

supabase: Client = create_client(url, key)
