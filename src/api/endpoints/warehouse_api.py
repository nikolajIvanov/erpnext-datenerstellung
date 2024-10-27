from src.api.base_api import BaseAPI


class WarehouseAPI(BaseAPI):

    def __init__(self):
        # Explicitly set the process type to avoid any automatic derivation
        super().__init__("warehouse")
        self.doctype = "Warehouse"
