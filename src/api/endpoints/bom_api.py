from src.api.base_api import BaseAPI


class BOMAPI(BaseAPI):

    def __init__(self):
        # Explicitly set the process type to avoid any automatic derivation
        super().__init__("bom")
        self.doctype = "BOM"
