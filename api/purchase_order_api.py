import logging

from .base_api import BaseAPI


class PurchaseOrderAPI(BaseAPI):
    def __init__(self):
        super().__init__()
        self.doctype = "Purchase Order"

    def get_all(self):
        return self._make_request("GET", self.doctype)

    def get(self, name):
        return self._make_request("GET", f"{self.doctype}/{name}")

    def create(self, data):
        logging.debug(f"Sending data to API: {data}")
        response = self._make_request("POST", self.doctype, data)
        logging.debug(f"API Response: {response}")
        return response

    def update(self, name, data):
        return self._make_request("PUT", f"{self.doctype}/{name}", data)

    def delete(self, name):
        return self._make_request("DELETE", f"{self.doctype}/{name}")