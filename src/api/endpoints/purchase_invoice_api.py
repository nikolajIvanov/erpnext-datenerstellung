from src.api.base_api import BaseAPI


class PurchaseInvoiceAPI(BaseAPI):

    def __init__(self):
        # Explicitly set the process type to avoid any automatic derivation
        super().__init__("purchase_invoice")
        self.doctype = "Purchase Invoice"
