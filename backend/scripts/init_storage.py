import asyncio
import sys
import os

# Add the parent directory to sys.path to allow imports from backend
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from supabase import create_client
from backend.config import settings
from backend.utils.logger import logger

def init_storage():
    """
    Initialize Supabase storage buckets.
    """
    try:
        logger.info("Initializing Supabase Storage...")
        
        # Use Service Role Key for admin tasks
        supabase = create_client(settings.SUPABASE_URL, settings.SUPABASE_SERVICE_ROLE_KEY)
        
        bucket_name = "documents"
        
        # List existing buckets
        buckets = supabase.storage.list_buckets()
        bucket_names = [b.name for b in buckets]
        
        if bucket_name in bucket_names:
            logger.info(f"Bucket '{bucket_name}' already exists.")
        else:
            logger.info(f"Creating bucket '{bucket_name}'...")
            supabase.storage.create_bucket(bucket_name, options={"public": False})
            logger.info(f"Bucket '{bucket_name}' created successfully.")
            
    except Exception as e:
        logger.error(f"Failed to initialize storage: {e}")
        print(f"Error: {e}")

if __name__ == "__main__":
    init_storage()
