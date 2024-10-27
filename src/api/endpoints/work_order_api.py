from src.api.base_api import BaseAPI


class WorkOrderAPI(BaseAPI):

    def __init__(self):
        # Explicitly set the process type to avoid any automatic derivation
        super().__init__("work_order")
        self.doctype = "Work Order"
