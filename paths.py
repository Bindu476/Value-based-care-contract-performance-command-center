"""
project/paths.py
Single source of truth for all filesystem paths in this project. Locates the project root
dynamically by walking up from this file's own location — this file always resolves correctly
because __file__ always points to wherever paths.py itself lives, regardless of which script
imports it, what the current working directory is, or where you extracted the project folder.

Every pipeline script, backend module, and test imports from here instead of hardcoding paths.
"""
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent

DATA_DIR = PROJECT_ROOT / "data"
DATA_RAW = DATA_DIR / "raw"
DATA_RAW_MSSP = DATA_RAW / "mssp"
DATA_RAW_HVBP = DATA_RAW / "hvbp"
DATA_RAW_PHYSICIAN = DATA_RAW / "physician"
DATA_PROCESSED = DATA_DIR / "processed"
DATA_ANALYTICAL = DATA_DIR / "analytical"

CONFIG_DIR = PROJECT_ROOT / "config"
MODELS_DIR = PROJECT_ROOT / "models"
BACKEND_DIR = PROJECT_ROOT / "backend"
REPORT_DIR = PROJECT_ROOT / "report"

# ensure the directories that scripts write into always exist
for _d in [DATA_PROCESSED, DATA_ANALYTICAL, MODELS_DIR / "aco", MODELS_DIR / "provider", MODELS_DIR / "hospital"]:
    _d.mkdir(parents=True, exist_ok=True)
