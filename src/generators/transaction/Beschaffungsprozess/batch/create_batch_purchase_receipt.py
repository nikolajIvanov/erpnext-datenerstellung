# src/generators/transaction/Beschaffungsprozess/batch/create_batch_purchase_receipt.py

from datetime import datetime, timedelta
from pathlib import Path
from typing import List, Dict, Tuple
import csv
import random
import logging

from src.api.endpoints.purchase_receipt_api import PurchaseReceiptAPI
from src.config.settings import (
    COMPANY, CURRENCY, CONVERSION_RATE, TARGET_WAREHOUSE,
    MASTER_DATA_DIR, OUTPUT_DIR
)


class BatchPurchaseReceiptGenerator:
    """Generator for purchase receipts in batch mode, controlled by master controller."""

    def __init__(self):
        self.logger = logging.getLogger('BatchPurchaseReceiptGenerator')
        self.api = PurchaseReceiptAPI()
        self.start_date = None
        self.end_date = None
        self.purchase_orders = None
        self._initialize_logging()

        # Store successful receipts in memory
        self.successful_receipts = []

        # Receipt specific configurations
        self.RECEIPT_DELAY_MIN = 1  # Minimum days after PO
        self.RECEIPT_DELAY_MAX = 14  # Maximum days after PO

    def _initialize_logging(self):
        """Initialize logging configuration"""
        self.logger = logging.getLogger(self.__class__.__name__)

        # Clear any existing handlers
        self.logger.handlers = []

        self.logger.setLevel(logging.INFO)
        formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')

        # Console Handler
        console_handler = logging.StreamHandler()
        console_handler.setFormatter(formatter)
        self.logger.addHandler(console_handler)

        # File Handler
        log_dir = OUTPUT_DIR / 'logs' / f'batch_{self.__class__.__name__.lower()}'
        log_dir.mkdir(parents=True, exist_ok=True)
        file_handler = logging.FileHandler(
            log_dir / f'batch_{datetime.now().strftime("%Y%m%d_%H%M%S")}.log'
        )
        file_handler.setFormatter(formatter)
        self.logger.addHandler(file_handler)

        # Prevent propagation to avoid duplicate logs
        self.logger.propagate = False

    def configure(self, start_date: datetime, end_date: datetime, purchase_orders: List[Dict]):
        """Configure the generator with parameters and purchase orders from master controller"""
        self.start_date = start_date
        self.end_date = end_date
        self.purchase_orders = purchase_orders
        self.logger.info(f"Configured batch generator for period: {start_date.date()} to {end_date.date()}, "
                         f"processing {len(purchase_orders)} purchase orders")

    def load_batch_info(self) -> Tuple[Dict[str, bool], Dict[str, str]]:
        """Load batch information for items"""
        try:
            # Load item batch flags
            batch_info = {}
            with open(MASTER_DATA_DIR / 'base' / 'items.csv', 'r', encoding='utf-8') as f:
                items = list(csv.DictReader(f))
                batch_info = {item['Item Code']: item.get('Has Batch No', '0') == '1'
                              for item in items}

            # Load batch numbers
            batch_numbers = {}
            with open(MASTER_DATA_DIR / 'base' / 'batch_numbers.csv', 'r', encoding='utf-8') as f:
                reader = csv.DictReader(f)
                batch_numbers = {row['Item']: row['Batch ID'] for row in reader}

            return batch_info, batch_numbers

        except Exception as e:
            self.logger.error(f"Error loading batch information: {str(e)}")
            raise

    def calculate_receipt_date(self, po_date: str) -> datetime:
        """Calculate receipt date based on PO date"""
        order_date = datetime.strptime(po_date, "%Y-%m-%d")
        delay_days = random.randint(self.RECEIPT_DELAY_MIN, self.RECEIPT_DELAY_MAX)
        receipt_date = order_date + timedelta(days=delay_days)

        # Ensure receipt date is within configured period
        if receipt_date > self.end_date:
            receipt_date = self.end_date

        return receipt_date

    def create_purchase_receipt(self, po: Dict, receipt_date: datetime,
                                batch_info: Dict[str, bool],
                                batch_numbers: Dict[str, str]) -> Dict:
        """Create a single purchase receipt document from purchase order"""
        item = po['items'][0]  # Assuming single item POs for now
        item_code = item['item_code']
        batch_no = batch_numbers.get(item_code, "") if batch_info.get(item_code, False) else ""

        return {
            "doctype": "Purchase Receipt",
            "naming_series": "MAT-PRE-.YYYY.-",
            "company": COMPANY,
            "currency": CURRENCY,
            "posting_date": receipt_date.strftime("%Y-%m-%d"),
            "posting_time": receipt_date.strftime("%H:%M:%S"),
            "conversion_rate": CONVERSION_RATE,
            "supplier": po['supplier'],
            "items": [{
                "item_code": item_code,
                "item_name": item['item_name'],
                "description": f"Receipt for {item['item_name']}",
                "received_qty": float(item['qty']),
                "qty": float(item['qty']),
                "rate": float(item['rate']),
                "amount": float(item['amount']),
                "uom": item['uom'],
                "stock_uom": item['stock_uom'],
                "conversion_factor": float(item['conversion_factor']),
                "batch_no": batch_no,
                "purchase_order": po['name'],
                "purchase_order_item": item['name'],
                "warehouse": TARGET_WAREHOUSE
            }],
            "taxes": [{
                "account_head": "1406 - Abziehbare Vorsteuer 19 % - B",
                "charge_type": "On Net Total",
                "description": "Abziehbare Vorsteuer 19 %",
                "rate": 19.0,
                "tax_amount": float(po['total_taxes_and_charges']),
                "total": float(po['grand_total'])
            }],
            "status": "To Bill",
            "docstatus": 1
        }

    def generate_and_upload(self) -> List[Dict]:
        """Generate and upload purchase receipts in batch"""
        if not all([self.start_date, self.end_date, self.purchase_orders]):
            raise ValueError("Generator not configured. Call configure() first.")

        self.successful_receipts = []  # Reset successful receipts
        try:
            # Load batch information
            batch_info, batch_numbers = self.load_batch_info()

            if not self.purchase_orders:
                raise ValueError("No purchase orders provided to process")

            # Generate and upload receipts
            for i, po in enumerate(self.purchase_orders, 1):
                try:
                    receipt_date = self.calculate_receipt_date(po['transaction_date'])
                    receipt_doc = self.create_purchase_receipt(
                        po, receipt_date, batch_info, batch_numbers)

                    response = self.api.create(receipt_doc)

                    if response and 'data' in response:
                        content = response['data']
                        if 'name' in content:
                            receipt_doc['name'] = content['name']
                            receipt_doc['api_response'] = content  # Store complete API response
                            receipt_doc['purchase_order_reference'] = po['name']  # Store reference to PO
                            if 'items' in content:
                                for idx, item in enumerate(receipt_doc['items']):
                                    item['name'] = content['items'][idx]['name']
                            self.successful_receipts.append(receipt_doc)
                            self.logger.info(
                                f"Successfully created PR {content['name']} ({i}/{len(self.purchase_orders)})")

                except Exception as e:
                    self.logger.error(f"Error processing receipt {i}: {str(e)}")
                    continue

            self.logger.info(f"Completed batch with {len(self.successful_receipts)} successful uploads "
                             f"out of {len(self.purchase_orders)} attempts")
            return self.successful_receipts

        except Exception as e:
            self.logger.error(f"Batch processing error: {str(e)}")
            raise

    def get_successful_receipts(self) -> List[Dict]:
        """Return the list of successful receipts for next process step"""
        return self.successful_receipts

    def save_to_csv(self, filename: str = 'batch_purchase_receipts.csv'):
        """Save batch results to CSV"""
        if not self.successful_receipts:
            self.logger.warning("No data to save to CSV.")
            return

        try:
            output_path = OUTPUT_DIR / filename

            rows = []
            for pr in self.successful_receipts:
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
                    rows.append(row)

            with open(output_path, 'w', newline='', encoding='utf-8') as f:
                writer = csv.DictWriter(f, fieldnames=rows[0].keys())
                writer.writeheader()
                writer.writerows(rows)

            self.logger.info(f"Successfully saved {len(rows)} records to {filename}")

        except Exception as e:
            self.logger.error(f"Error saving to CSV: {str(e)}")
            raise

    def process(self) -> bool:
        """Main batch processing method called by master controller"""
        try:
            self.logger.info(f"Starting batch purchase receipt process for period: "
                             f"{self.start_date.date()} to {self.end_date.date()}")

            # Generate and upload receipts
            self.generate_and_upload()

            # Save results if any successful uploads
            if self.successful_receipts:
                self.save_to_csv()
                return True
            else:
                self.logger.warning("No successful receipts to save.")
                return False

        except Exception as e:
            self.logger.error(f"Batch process failed: {str(e)}")
            return False