import csv
from datetime import datetime, timedelta
import random
from pathlib import Path
from typing import List, Dict, Tuple
import json
from src.api.endpoints.purchase_order_api import PurchaseOrderAPI
from src.core.base_transaction import BaseConfig
from src.core.logging import ProcessLogger
from src.config.settings import (
    COMPANY, CURRENCY, CONVERSION_RATE, TARGET_WAREHOUSE,
    MASTER_DATA_DIR, OUTPUT_DIR
)


class PurchaseOrderConfig(BaseConfig):
    """Configuration specific to purchase order process."""

    def __init__(self):
        super().__init__('purchase_orders')

        # Process-specific settings
        self.START_DATE = datetime.now() - timedelta(days=5 * 365)
        self.END_DATE = datetime.now()
        self.NUM_ORDERS = 5
        self.MAPPING_FILE = MASTER_DATA_DIR / 'mappings' / 'item_supplier_mapping.csv'


class PurchaseOrderGenerator:
    def __init__(self):
        self.config = PurchaseOrderConfig()
        self.logger = ProcessLogger(self.config)
        self.api = PurchaseOrderAPI()

    def upload_purchase_order_to_api(self, purchase_order: Dict) -> Tuple[bool, str, Dict]:
        """Upload purchase order to API with improved error handling."""
        try:
            response = self.api.create(purchase_order)

            if not response or 'data' not in response:
                return False, "", {}

            content = response['data']

            if isinstance(content, dict) and 'name' in content:
                system_id = content['name']
                self.logger.log_info(f"Successfully created Purchase Order with ID: {system_id}")
                return True, system_id, content

            return False, "", {}

        except Exception:
            return False, "", {}

    def load_csv_data(self, filename: str) -> List[Dict]:
        """Load data from a CSV file."""
        try:
            filepath = MASTER_DATA_DIR / 'base' / filename
            self.logger.log_info(f"Loading CSV file from: {filepath}")
            with open(filepath, 'r', encoding='utf-8') as f:
                return list(csv.DictReader(f))
        except Exception as e:
            self.logger.log_error(f"Error loading CSV file {filename}: {str(e)}")
            raise


    def load_item_supplier_mapping(self) -> Dict[str, str]:
        """Load item-supplier mapping from CSV."""
        mapping = {}
        try:
            if self.config.MAPPING_FILE.exists():
                with open(self.config.MAPPING_FILE, 'r', encoding='utf-8') as f:
                    reader = csv.DictReader(f)
                    for row in reader:
                        mapping[row['Item Code']] = row['Supplier ID']
            return mapping
        except Exception as e:
            self.logger.log_error(f"Error loading supplier mapping: {str(e)}")
            raise

    @staticmethod
    def random_date(start_date: datetime, end_date: datetime) -> datetime:
        """Generate a random date between start_date and end_date."""
        return start_date + timedelta(
            seconds=random.randint(0, int((end_date - start_date).total_seconds()))
        )

    @staticmethod
    def calculate_taxes(net_amount: float, tax_rate: float = 19.0) -> Tuple[float, float]:
        """Calculate tax amount and gross amount."""
        tax_amount = net_amount * (tax_rate / 100)
        gross_amount = net_amount + tax_amount
        return round(tax_amount, 2), round(gross_amount, 2)

    @staticmethod
    def filter_components(products: List[Dict]) -> List[Dict]:
        """Filter products to include only bicycle components."""
        return [product for product in products if product['Item Group'] == 'Fahrradkomponenten']

    def generate_purchase_orders(self, products: List[Dict], item_supplier_mapping: Dict[str, str]) -> List[Dict]:
        """Generate purchase order documents."""
        purchase_orders = []
        for _ in range(self.config.NUM_ORDERS):
            try:
                po_date = self.random_date(self.config.START_DATE, self.config.END_DATE)
                product = random.choice(products)
                item_code = product['Item Code']

                supplier_id = item_supplier_mapping.get(item_code)
                if not supplier_id:
                    self.logger.log_warning(f"No supplier found for item {item_code}, skipping...")
                    continue

                quantity = 500
                rate = float(product['Valuation Rate'])
                net_amount = round(quantity * rate, 2)
                tax_amount, gross_amount = self.calculate_taxes(net_amount)

                po = {
                    "doctype": "Purchase Order",
                    "naming_series": 1,
                    # "naming_series": "PUR-ORD-.YYYY.-",
                    "company": COMPANY,
                    "currency": CURRENCY,
                    "transaction_date": po_date.strftime("%Y-%m-%d"),
                    "schedule_date": (po_date + timedelta(days=7)).strftime("%Y-%m-%d"),
                    "conversion_rate": CONVERSION_RATE,
                    "supplier": supplier_id,
                    "supplier_name": f"Purchase Order for {supplier_id}",
                    "items": [{
                        "item_code": item_code,
                        "item_name": product['Item Name'],
                        "description": product.get('Description', ''),
                        "qty": quantity,
                        "rate": rate,
                        "amount": net_amount,
                        "uom": product['Default Unit of Measure'],
                        "stock_uom": product['Default Unit of Measure'],
                        "conversion_factor": 1.0,
                        "warehouse": TARGET_WAREHOUSE
                    }],
                    "taxes": [{
                        "charge_type": "On Net Total",
                        "account_head": "1406 - Abziehbare Vorsteuer 19 % - B",
                        "description": "Abziehbare Vorsteuer 19 %",
                        "rate": 19.0
                    }],
                    "total_taxes_and_charges": tax_amount,
                    "grand_total": gross_amount,
                    "rounded_total": round(gross_amount),
                    "status": "Draft",
                    "docstatus": 0
                }

                purchase_orders.append(po)

            except Exception as e:
                self.logger.log_error(f"Error generating purchase order: {str(e)}")
                continue

        return purchase_orders

    def save_to_csv(self, data: List[Dict], filename: str):
        """Save purchase orders to CSV file."""
        if not data:
            self.logger.log_warning("No data to save to CSV.")
            return

        try:
            flattened_data = []
            for po in data:
                for item in po['items']:
                    row = {
                        "ID": po['name'],
                        "Company": po['company'],
                        "Currency": po['currency'],
                        "Date": po['transaction_date'],
                        "Exchange Rate": "1,00",
                        "Series": po['naming_series'],
                        "Status": po['status'],
                        "Supplier": po['supplier'],
                        "Title": po['supplier_name'],
                        "ID (Items)": item.get('name', ''),
                        "Amount (Items)": item['amount'],
                        "Item Code (Items)": item['item_code'],
                        "Item Name (Items)": item['item_name'],
                        "Quantity (Items)": item['qty'],
                        "Rate (Items)": item['rate'],
                        "Required By (Items)": po['schedule_date'],
                        "Stock UOM (Items)": item['stock_uom'],
                        "UOM (Items)": item['uom'],
                        "UOM Conversion Factor (Items)": item['conversion_factor'],
                        "Set Target Warehouse": item['warehouse'],
                        "Net Total": f"{item['amount']:.2f}".replace('.', ','),
                        "Total Taxes and Charges": f"{po['total_taxes_and_charges']:.2f}".replace('.', ','),
                        "Grand Total": f"{po['grand_total']:.2f}".replace('.', ','),
                        "Rounded Total": f"{po['rounded_total']:.2f}".replace('.', ','),
                    }
                    flattened_data.append(row)

            output_path = OUTPUT_DIR / filename

            with open(output_path, 'w', newline='', encoding='utf-8') as f:
                writer = csv.DictWriter(f, fieldnames=flattened_data[0].keys())
                writer.writeheader()
                writer.writerows(flattened_data)

            self.logger.log_info(f"Successfully saved data to {filename}")

        except Exception as e:
            self.logger.log_error(f"Error saving to CSV: {str(e)}")
            raise

    def process(self):
        """Main process for generating and uploading purchase orders."""
        try:
            # Load and prepare data
            products = self.load_csv_data('items.csv')
            components = self.filter_components(products)
            item_supplier_mapping = self.load_item_supplier_mapping()

            # Generate purchase orders
            purchase_orders = self.generate_purchase_orders(components, item_supplier_mapping)

            # Upload and track successful uploads
            successful_uploads = []
            for po in purchase_orders:
                success, system_id, response_data = self.upload_purchase_order_to_api(po)
                if success:
                    po['name'] = system_id
                    if 'items' in response_data:
                        for i, item in enumerate(po['items']):
                            item['name'] = response_data['items'][i]['name']
                    successful_uploads.append(po)

            # Save results
            if successful_uploads:
                self.save_to_csv(successful_uploads, 'purchase_orders.csv')
            else:
                self.logger.log_warning("No successful uploads to save to CSV.")

        except Exception as e:
            self.logger.log_error(f"Process Error: {str(e)}")
            raise


def main():
    generator = PurchaseOrderGenerator()
    generator.process()


if __name__ == "__main__":
    main()
