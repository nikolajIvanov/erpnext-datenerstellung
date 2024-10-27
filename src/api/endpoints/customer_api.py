from src.api.base_api import BaseAPI


class CustomerAPI(BaseAPI):

    def __init__(self):
        # Explicitly set the process type to avoid any automatic derivation
        super().__init__("customer")
        self.doctype = "Customer"
