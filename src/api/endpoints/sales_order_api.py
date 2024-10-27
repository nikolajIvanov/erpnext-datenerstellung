from src.api.base_api import BaseAPI


class SalesOrderAPI(BaseAPI):

    def __init__(self):
        # Explicitly set the process type to avoid any automatic derivation
        super().__init__("sales_order")
        self.doctype = "Sales Order"
