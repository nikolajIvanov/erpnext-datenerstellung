import json
from datetime import datetime
from pathlib import Path

import requests
from typing import Dict, Any, Optional

from src.config.api_config import BASE_URL, API_KEY
from src.core.base_transaction import BaseConfig
from src.core.logging import ProcessLogger


class BaseAPI:
    def __init__(self, process_type: Optional[str] = None):
        if process_type is None:
            process_type = self.__class__.__name__.replace('API', '').lower()

        self.config = BaseConfig(process_type)
        self.logger = ProcessLogger(self.config)
        self.base_url = BASE_URL
        self.api_key = API_KEY
        self.headers = {
            "Authorization": f"token {self.api_key}",
            "Accept": "application/json",
            "Content-Type": "application/json"
        }

    def save_failed_api_payload(self, endpoint: str, payload: Dict[str, Any],
                                error_message: str, response: Optional[requests.Response] = None) -> Path:
        """Save failed API payload and response details."""
        identifier = datetime.now().strftime("%Y%m%d_%H%M%S")
        file_path = self.config.get_api_payload_path(identifier)

        error_payload = {
            "error_message": error_message,
            "timestamp": datetime.now().isoformat(),
            "endpoint": endpoint,
            "request": {
                "url": f"{self.base_url}/resource/{endpoint}",
                "headers": {k: v for k, v in self.headers.items() if k != "Authorization"},
                "payload": payload
            }
        }

        if response:
            error_payload["response"] = {
                "status_code": response.status_code,
                "headers": dict(response.headers),
                "body": response.text
            }

        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(error_payload, f, indent=2, ensure_ascii=False)

        return file_path

    def _make_request(self, method: str, endpoint: str, data: Optional[Dict] = None) -> Dict[str, Any]:
        """Make an API request with improved error handling."""
        url = f"{self.base_url}/resource/{endpoint}"

        try:
            response = requests.request(
                method=method,
                url=url,
                json=data,
                headers=self.headers,
                verify=True
            )

            try:
                response_data = response.json()
            except json.JSONDecodeError:
                response_data = {"text": response.text}

            if response.ok:
                if isinstance(response_data, dict):
                    if "message" in response_data:
                        return {"data": response_data["message"]}
                    elif "data" in response_data:
                        return {"data": response_data["data"]}
                    else:
                        return {"data": response_data}
                return {"data": response_data}

            error_msg = f"API request failed: {response.status_code}"
            error_path = self.save_failed_api_payload(
                endpoint=endpoint,
                payload=data,
                error_message=error_msg,
                response=response
            )
            self.logger.log_error(f"Request failed: {error_msg}")
            raise requests.exceptions.RequestException(error_msg)

        except Exception as e:
            if not isinstance(e, requests.exceptions.RequestException):
                error_msg = f"Request error: {str(e)}"
                error_path = self.save_failed_api_payload(
                    endpoint=endpoint,
                    payload=data,
                    error_message=error_msg
                )
                self.logger.log_error(error_msg)
            raise

    def create(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Create a new document via API."""
        try:
            return self._make_request("POST", self.doctype, data)
        except Exception:
            raise