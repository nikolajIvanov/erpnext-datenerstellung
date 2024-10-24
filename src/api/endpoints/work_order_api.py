from src.api.base_api import BaseAPI


class WorkOrderAPI(BaseAPI):
    def __init__(self):
        super().__init__()
        self.doctype = "Work Order"

    def get_all(self):
        return self._make_request("GET", self.doctype)

    def get(self, name):
        return self._make_request("GET", f"{self.doctype}/{name}")

    def create(self, data):
        return self._make_request("POST", self.doctype, data)

    def update(self, name, data):
        return self._make_request("PUT", f"{self.doctype}/{name}", data)

    def delete(self, name):
        return self._make_request("DELETE", f"{self.doctype}/{name}")