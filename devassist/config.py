# Developer Assist configuration
import os
from pathlib import Path
from dotenv import load_dotenv

load_dotenv(dotenv_path=Path("C:/Users/pjeni/devassist/.env"))

GROQ_API_KEY = os.getenv("GROQ_API_KEY")
CHROMA_DB_PATH = "./chroma_store"
COLLECTION_NAME = "devassist_code"

SUPPORTED_EXTENSIONS = [
    ".py", ".js", ".ts", ".jsx", ".tsx",
    ".java", ".cpp", ".c", ".go", ".rs"
]