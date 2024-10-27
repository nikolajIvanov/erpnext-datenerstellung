from src.api.base_api import BaseAPI


class MaterialRequestAPI(BaseAPI):

    def __init__(self):
        # Explicitly set the process type to avoid any automatic derivation
        super().__init__("material_request")
        self.doctype = "Material Request"
