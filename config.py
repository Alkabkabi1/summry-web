from pathlib import Path

APP_ROOT = Path(__file__).resolve().parent
DATA_DIR = APP_ROOT / "data"
SUBJECTS_DIR = DATA_DIR / "subjects"
SUBJECTS_JSON = DATA_DIR / "subjects.json"

MAX_UPLOAD_MB = 50
ALLOWED_EXTENSIONS = {".pdf"}
