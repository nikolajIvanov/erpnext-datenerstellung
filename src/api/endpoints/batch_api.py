from src.api.base_api import BaseAPI


class BatchNoAPI(BaseAPI):

    def __init__(self):
        # Explicitly set the process type to avoid any automatic derivation
        super().__init__("batch_no")
        self.doctype = "Batch No"
