from src.api.base_api import BaseAPI


class PurchaseOrderAPI(BaseAPI):
    """API endpoint for Purchase Order operations."""

    def __init__(self):
        # Explicitly set the process type to avoid any automatic derivation
        super().__init__("purchase_orders")
        self.doctype = "Purchase Order"
