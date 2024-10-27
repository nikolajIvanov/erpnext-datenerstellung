from src.api.base_api import BaseAPI


class SerialNoAPI(BaseAPI):

    def __init__(self):
        # Explicitly set the process type to avoid any automatic derivation
        super().__init__("serial_no")
        self.doctype = "Serial No"
