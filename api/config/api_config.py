import os
from dotenv import load_dotenv

# .env Datei laden
load_dotenv()


BASE_URL = "https://bikeshop-erp-next.iuk.hdm-stuttgart.de/api"
API_KEY = os.getenv('ERP_API_KEY')
