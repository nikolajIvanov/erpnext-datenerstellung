import csv
from datetime import datetime, timedelta
import random
from typing import List, Dict, Tuple
from src.api.endpoints.purchase_receipt_api import PurchaseReceiptAPI
from src.core.base_transaction import BaseConfig
from src.core.logging import ProcessLogger
from src.config.settings import (
    COMPANY, CURRENCY, CONVERSION_RATE, TARGET_WAREHOUSE,
    MASTER_DATA_DIR, OUTPUT_DIR
)


class PurchaseReceiptConfig(BaseConfig):
    """Configuration specific to purchase receipt process."""

    def __init__(self):
        super().__init__('purchase_receipt')

        # Process-specific settings
        self.RECEIPT_DELAY = (1, 14)  # Receipt 1-14 days after order


class PurchaseReceiptGenerator:
    def __init__(self):
        self.config = PurchaseReceiptConfig()
        self.logger = ProcessLogger(self.config)
        self.api = PurchaseReceiptAPI()

    def upload_purchase_receipt_to_api(self, purchase_receipt: Dict) -> Tuple[bool, str, Dict]:
        """Upload purchase receipt to API with improved error handling."""
        try:
            response = self.api.create(purchase_receipt)

            if not response or 'data' not in response:
                return False, "", {}

            content = response['data']

            if isinstance(content, dict) and 'name' in content:
                system_id = content['name']
                self.logger.log_info(f"Successfully created Purchase Receipt with ID: {system_id}")
                return True, system_id, content

            return False, "", {}

        except Exception as e:
            self.logger.log_error(f"Failed to upload Purchase Receipt: {str(e)}")
            return False, "", {}

    def load_csv_data(self, filename: str) -> List[Dict]:
        """Load data from a CSV file."""
        try:
            filepath = OUTPUT_DIR / filename
            self.logger.log_info(f"Loading CSV file from: {filepath}")
            with open(filepath, 'r', encoding='utf-8') as f:
                return list(csv.DictReader(f))
        except Exception as e:
            self.logger.log_error(f"Error loading CSV file {filename}: {str(e)}")
            raise

    def load_item_batch_info(self) -> Dict[str, bool]:
        """Load batch information for items."""
        try:
            filepath = MASTER_DATA_DIR / 'base' / 'items.csv'
            with open(filepath, 'r', encoding='utf-8') as f:
                items = list(csv.DictReader(f))
                return {item['Item Code']: item.get('Has Batch No', '0') == '1' for item in items}
        except Exception as e:
            self.logger.log_error(f"Error loading batch info: {str(e)}")
            raise

    def load_batch_numbers(self) -> Dict[str, str]:
        """Load batch number mappings."""
        try:
            filepath = MASTER_DATA_DIR / 'base' / 'batch_numbers.csv'
            batch_numbers = {}
            with open(filepath, 'r', encoding='utf-8') as f:
                reader = csv.DictReader(f)
                for row in reader:
                    batch_numbers[row['Item']] = row['Batch ID']
            return batch_numbers
        except Exception as e:
            self.logger.log_error(f"Error loading batch numbers: {str(e)}")
            raise

    def generate_purchase_receipts(self, purchase_orders: List[Dict], item_batch_info: Dict[str, bool],
                                   batch_numbers: Dict[str, str]) -> List[Dict]:
        """Generate purchase receipt documents."""
        purchase_receipts = []
        for po in purchase_orders:
            try:
                po_date = datetime.strptime(po['Date'], "%Y-%m-%d")
                pr_date = po_date + timedelta(days=random.randint(*self.config.RECEIPT_DELAY))
                item_code = po['Item Code (Items)']
                batch_no = batch_numbers.get(item_code, "") if item_batch_info.get(item_code, False) else ""

                receipt = {
                    "doctype": "Purchase Receipt",
                    "naming_series": "MAT-PRE-.YYYY.-",
                    "company": COMPANY,
                    "currency": CURRENCY,
                    "posting_date": pr_date.strftime("%Y-%m-%d"),
                    "posting_time": pr_date.strftime("%H:%M:%S.%f"),
                    "conversion_rate": CONVERSION_RATE,
                    "supplier": po['Supplier'],
                    "items": [{
                        "item_code": item_code,
                        "item_name": po['Item Name (Items)'],
                        "description": f"Receipt for {po['Item Name (Items)']}",
                        "received_qty": float(po['Quantity (Items)']),
                        "qty": float(po['Quantity (Items)']),
                        "rate": float(po['Rate (Items)']),
                        "amount": float(po['Amount (Items)']),
                        "uom": po['UOM (Items)'],
                        "stock_uom": po['Stock UOM (Items)'],
                        "conversion_factor": 1.0,
                        "batch_no": batch_no,
                        "purchase_order": po['ID'],
                        "purchase_order_item": po['ID (Items)'],
                        "warehouse": TARGET_WAREHOUSE
                    }],
                    "taxes": [{
                        "account_head": "1406 - Abziehbare Vorsteuer 19 % - B",
                        "charge_type": "On Net Total",
                        "description": "Abziehbare Vorsteuer 19 %",
                        "rate": 19.0,
                        "tax_amount": float(po['Total Taxes and Charges'].replace(',', '.')),
                        "total": float(po['Grand Total'].replace(',', '.'))
                    }],
                    "status": "To Bill",
                    "docstatus": 1
                }
                purchase_receipts.append(receipt)

            except Exception as e:
                self.logger.log_error(f"Error generating purchase receipt: {str(e)}")
                continue

        return purchase_receipts

    def save_to_csv(self, data: List[Dict], filename: str):
        """Save purchase receipts to CSV file."""
        if not data:
            self.logger.log_warning("No data to save to CSV.")
            return

        try:
            flattened_data = []
            for pr in data:
                for item in pr['items']:
                    row = {
                        "ID": pr['name'],
                        "Company": pr['company'],
                        "Currency": pr['currency'],
                        "Date": pr['posting_date'],
                        "Exchange Rate": "1,00",
                        "Net Total (Company Currency)": item['amount'],
                        "Posting Time": pr['posting_time'],
                        "Series": pr['naming_series'],
                        "Status": pr['status'],
                        "Supplier": pr['supplier'],
                        "ID (Items)": item.get('name', ''),
                        "Conversion Factor (Items)": item['conversion_factor'],
                        "Item Code (Items)": item['item_code'],
                        "Item Name (Items)": item['item_name'],
                        "Rate (Company Currency) (Items)": item['rate'],
                        "Received Quantity (Items)": item['received_qty'],
                        "Stock UOM (Items)": item['stock_uom'],
                        "UOM (Items)": item['uom'],
                        "Purchase Order (Items)": item['purchase_order'],
                        "Purchase Order Item (Items)": item['purchase_order_item'],
                        "Accepted Warehouse (Items)": item['warehouse'],
                        "Tax Rate (Purchase Taxes and Charges)": pr['taxes'][0]['rate'],
                        "Account Head (Purchase Taxes and Charges)": pr['taxes'][0]['account_head'],
                        "Accepted Quantity (Items)": item['qty'],
                        "Description (Purchase Taxes and Charges)": pr['taxes'][0]['description'],
                        "Type (Purchase Taxes and Charges)": pr['taxes'][0]['charge_type'],
                        "Add or Deduct (Purchase Taxes and Charges)": "Add",
                        "Consider Tax or Charge for (Purchase Taxes and Charges)": "Total",
                        "Batch No (Items)": item['batch_no']
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
        """Main process for generating and uploading purchase receipts."""
        try:
            # Load and prepare data
            purchase_orders = self.load_csv_data('purchase_orders.csv')
            item_batch_info = self.load_item_batch_info()
            batch_numbers = self.load_batch_numbers()

            # Generate purchase receipts
            purchase_receipts = self.generate_purchase_receipts(purchase_orders, item_batch_info, batch_numbers)

            # Upload and track successful uploads
            successful_uploads = []
            for pr in purchase_receipts:
                success, system_id, response_data = self.upload_purchase_receipt_to_api(pr)
                if success:
                    pr['name'] = system_id
                    if 'items' in response_data:
                        for i, item in enumerate(pr['items']):
                            item['name'] = response_data['items'][i]['name']
                    successful_uploads.append(pr)

            # Save results
            if successful_uploads:
                self.save_to_csv(successful_uploads, 'purchase_receipts.csv')
            else:
                self.logger.log_warning("No successful uploads to save to CSV.")

        except Exception as e:
            self.logger.log_error(f"Process Error: {str(e)}")
            raise


def main():
    generator = PurchaseReceiptGenerator()
    generator.process()


if __name__ == "__main__":
    main()