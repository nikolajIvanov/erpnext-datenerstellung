import os
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def get_project_root() -> Path:
    """Get the project root directory."""
    current_dir = Path(__file__).resolve().parent.parent.parent
    return current_dir

# Project structure
PROJECT_ROOT = get_project_root()
DATA_DIR = PROJECT_ROOT / 'data'
INPUT_DIR = DATA_DIR / 'generated'
OUTPUT_DIR = DATA_DIR / 'generated'
MASTER_DATA_DIR = DATA_DIR / 'master'
LOG_DIR = PROJECT_ROOT / 'logs'
PROCESS_LOGS_DIR = LOG_DIR / 'process_logs'
API_PAYLOAD_DIR = LOG_DIR / 'api_payloads'

# Company settings
COMPANY = "Velo GmbH"
CURRENCY = "EUR"
TARGET_WAREHOUSE = "Lager Stuttgart - B"
CONVERSION_RATE = 1.0

# API settings
API_BASE_URL = "https://bikeshop-erp-next.iuk.hdm-stuttgart.de/api"
API_KEY = os.getenv('ERP_API_KEY')

# Ensure required directories exist
for directory in [INPUT_DIR, OUTPUT_DIR, MASTER_DATA_DIR, LOG_DIR, PROCESS_LOGS_DIR, API_PAYLOAD_DIR]:
    directory.mkdir(parents=True, exist_ok=True)