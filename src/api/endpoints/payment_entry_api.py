from src.api.base_api import BaseAPI


class PaymentEntryAPI(BaseAPI):

    def __init__(self):
        # Explicitly set the process type to avoid any automatic derivation
        super().__init__("payment_entry")
        self.doctype = "Payment Entry"
