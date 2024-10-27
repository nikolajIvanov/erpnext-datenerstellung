from datetime import datetime
from pathlib import Path
from src.config import settings


class BaseConfig:
    def __init__(self, process_type: str):
        self.process_type = process_type.rstrip('s') + 's'
        self.LOG_DIR = settings.LOG_DIR / 'process_logs' / self.process_type
        self.API_PAYLOAD_DIR = settings.API_PAYLOAD_DIR / self.process_type

        self.LOG_DIR.mkdir(parents=True, exist_ok=True)
        self.API_PAYLOAD_DIR.mkdir(parents=True, exist_ok=True)

    def get_log_file_path(self) -> Path:
        """Generate log file path with timestamp."""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        return self.LOG_DIR / f'{self.process_type}_{timestamp}.log'

    def get_api_payload_path(self, identifier: str) -> Path:
        """Generate API payload file path."""
        return self.API_PAYLOAD_DIR / f"failed_{identifier}.json"