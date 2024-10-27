from src.api.base_api import BaseAPI


class DeliveryNoteAPI(BaseAPI):

    def __init__(self):
        # Explicitly set the process type to avoid any automatic derivation
        super().__init__("delivery_note")
        self.doctype = "Delivery Note"
