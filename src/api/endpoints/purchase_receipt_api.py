from src.api.base_api import BaseAPI


class PurchaseReceiptAPI(BaseAPI):

    def __init__(self):
        # Explicitly set the process type to avoid any automatic derivation
        super().__init__("purchase_receipt")
        self.doctype = "Purchase Receipt"
