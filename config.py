import os
from dotenv import load_dotenv

def setup_environment():
    load_dotenv()

API_TOKEN = os.getenv('TELEGRAM_API_TOKEN')
GROUP_CHAT_ID = os.getenv('GROUP_CHAT_ID')
MESSAGE_THREAD_ID = os.getenv('MESSAGE_THREAD_ID')
SUPABASE_URL = os.getenv('SUPABASE_URL')
SUPABASE_KEY = os.getenv('SUPABASE_KEY')
