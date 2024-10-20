import requests
from config.api_config import BASE_URL, API_KEY


class BaseAPI:
    def __init__(self):
        self.base_url = BASE_URL
        self.api_key = API_KEY
        self.headers = {
            "Authorization": f"token {self.api_key}",
            "Content-Type": "application/json"
        }

    def _make_request(self, method, endpoint, data=None):
        url = f"{self.base_url}/resource/{endpoint}"
        response = requests.request(method, url, json=data, headers=self.headers)
        response.raise_for_status()
        return response.json()
