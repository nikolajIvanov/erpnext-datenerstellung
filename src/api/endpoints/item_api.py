from src.api.base_api import BaseAPI


class ItemAPI(BaseAPI):

    def __init__(self):
        # Explicitly set the process type to avoid any automatic derivation
        super().__init__("item")
        self.doctype = "Item"
