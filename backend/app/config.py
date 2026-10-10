from pathlib import Path
import os

try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

BASE_DIR = Path(__file__).resolve().parent.parent
UPLOAD_DIR = BASE_DIR / "uploads"
UPLOAD_DIR.mkdir(exist_ok=True)

CHROMA_DIR = BASE_DIR / "chroma_data"
CHROMA_DIR.mkdir(exist_ok=True)

MAX_UPLOAD_MB = 50

CHUNK_MAX_CHARS = 800
CHUNK_OVERLAP_CHARS = 80
RETRIEVE_TOP_K = 5

DEEPSEEK_API_KEY = os.environ.get("DEEPSEEK_API_KEY", "")
DEEPSEEK_BASE_URL = "https://api.deepseek.com/v1"
DEEPSEEK_MODEL = "deepseek-chat"