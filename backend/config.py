"""
Centralized configuration — loads .env once and exports values.
Every module should import from here instead of calling os.getenv() directly.
"""
import os
from pathlib import Path
from dotenv import load_dotenv

# Load from backend/.env first, then fall back to parent directory .env
_backend_env = Path(__file__).resolve().parent / '.env'
_root_env = Path(__file__).resolve().parent.parent / '.env'

load_dotenv(_root_env, override=False)  # load root first (lower priority)
load_dotenv(_backend_env, override=True) # load backend/.env (higher priority)

# ── Google OAuth ─────────────────────────────────────────────────────────
GOOGLE_CLIENT_ID = os.getenv('GOOGLE_CLIENT_ID', '')

# ── App Secret ───────────────────────────────────────────────────────────
SECRET_KEY = os.getenv('SECRET_KEY', 'your-secret-key')

# ── Mail ─────────────────────────────────────────────────────────────────
MAIL_USERNAME = os.getenv('MAIL_USERNAME')
MAIL_PASSWORD = os.getenv('MAIL_PASSWORD')
MAIL_DEFAULT_SENDER = os.getenv('MAIL_DEFAULT_SENDER')

# ── Database ─────────────────────────────────────────────────────────────
# IMPORTANT: On Render, set MONGO_URI to your MongoDB Atlas connection string!
# Example: mongodb+srv://user:pass@cluster0.xxxxx.mongodb.net/aura_db?retryWrites=true&w=majority
MONGO_URI = os.getenv('MONGO_URI', 'mongodb://localhost:27017/')

# ── AI Keys ──────────────────────────────────────────────────────────────
GEMINI_API_KEY = os.getenv('GEMINI_API_KEY', '')
OPENROUTER_API_KEY = os.getenv('OPENROUTER_API_KEY', '')

# ── Supabase ─────────────────────────────────────────────────────────────
# Support both SUPABASE_URL and VITE_SUPABASE_URL (frontend uses VITE_ prefix)
SUPABASE_URL = os.getenv('SUPABASE_URL') or os.getenv('VITE_SUPABASE_URL', '')
SUPABASE_ANON_KEY = os.getenv('SUPABASE_ANON_KEY') or os.getenv('VITE_SUPABASE_PUBLISHABLE_DEFAULT_KEY', '')
SUPABASE_JWT_SECRET = os.getenv('SUPABASE_JWT_SECRET', '')

print(f"[Config] MONGO_URI starts with: {MONGO_URI[:30]}...")
print(f"[Config] SUPABASE_URL: {SUPABASE_URL}")
print(f"[Config] SUPABASE_JWT_SECRET length: {len(SUPABASE_JWT_SECRET)}")
