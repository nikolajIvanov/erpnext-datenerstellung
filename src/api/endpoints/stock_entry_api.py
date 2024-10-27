from src.api.base_api import BaseAPI


class StockEntryAPI(BaseAPI):

    def __init__(self):
        # Explicitly set the process type to avoid any automatic derivation
        super().__init__("stock_entry")
        self.doctype = "Stock Entry"
