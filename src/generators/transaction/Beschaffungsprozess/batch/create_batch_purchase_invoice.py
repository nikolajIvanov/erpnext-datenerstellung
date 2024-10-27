# src/generators/transaction/Beschaffungsprozess/batch/create_batch_purchase_invoice.py

from datetime import datetime, timedelta
from pathlib import Path
from typing import List, Dict, Tuple
import csv
import random
import logging

from src.api.endpoints.purchase_invoice_api import PurchaseInvoiceAPI
from src.config.settings import (
    COMPANY, CURRENCY, CONVERSION_RATE,
    MASTER_DATA_DIR, OUTPUT_DIR
)


class BatchPurchaseInvoiceGenerator:
    """Generator for purchase invoices in batch mode, controlled by master controller."""

    def __init__(self):
        self.logger = logging.getLogger('BatchPurchaseInvoiceGenerator')
        self.api = PurchaseInvoiceAPI()
        self.start_date = None
        self.end_date = None
        self.purchase_receipts = None
        self._initialize_logging()

        # Store successful invoices in memory
        self.successful_invoices = []

        # Invoice specific configurations
        self.INVOICE_DELAY_MIN = 0  # Minimum days after receipt
        self.INVOICE_DELAY_MAX = 3  # Maximum days after receipt

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

    def configure(self, start_date: datetime, end_date: datetime, purchase_receipts: List[Dict]):
        """Configure the generator with parameters and purchase receipts from master controller"""
        self.start_date = start_date
        self.end_date = end_date
        self.purchase_receipts = purchase_receipts
        self.logger.info(f"Configured batch generator for period: {start_date.date()} to {end_date.date()}, "
                         f"processing {len(purchase_receipts)} purchase receipts")

    def calculate_invoice_date(self, receipt_date: str) -> datetime:
        """Calculate invoice date based on receipt date"""
        base_date = datetime.strptime(receipt_date, "%Y-%m-%d")
        delay_days = random.randint(self.INVOICE_DELAY_MIN, self.INVOICE_DELAY_MAX)
        invoice_date = base_date + timedelta(days=delay_days)

        # Ensure invoice date is within configured period
        if invoice_date > self.end_date:
            invoice_date = self.end_date

        return invoice_date

    def create_purchase_invoice(self, pr: Dict, invoice_date: datetime) -> Dict:
        """Create a single purchase invoice document from purchase receipt"""
        item = pr['items'][0]  # Assuming single item receipts for now
        due_date = invoice_date + timedelta(days=30)  # Standard 30 days payment term

        return {
            "doctype": "Purchase Invoice",
            "naming_series": "ACC-PINV-.YYYY.-",
            "company": COMPANY,
            "currency": CURRENCY,
            "conversion_rate": CONVERSION_RATE,
            "posting_date": invoice_date.strftime("%Y-%m-%d"),
            "posting_time": invoice_date.strftime("%H:%M:%S"),
            "due_date": due_date.strftime("%Y-%m-%d"),
            "bill_date": invoice_date.strftime("%Y-%m-%d"),
            "bill_no": f"BILL-{pr['name']}",
            "supplier": pr['supplier'],
            "credit_to": "3500 - Sonstige Verb. - B",
            "is_return": 0,
            "update_stock": 0,
            "items": [{
                "item_code": item['item_code'],
                "item_name": item['item_name'],
                "description": f"Invoice for {item['item_name']}",
                "received_qty": float(item['received_qty']),
                "qty": float(item['qty']),
                "uom": item['uom'],
                "stock_uom": item['stock_uom'],
                "conversion_factor": float(item['conversion_factor']),
                "rate": float(item['rate']),
                "amount": float(item['amount']),
                "base_rate": float(item['rate']),
                "base_amount": float(item['amount']),
                "purchase_order": item['purchase_order'],
                "po_detail": item['purchase_order_item'],
                "purchase_receipt": pr['name'],
                "pr_detail": item['name'],
                "warehouse": item['warehouse'],
                "expense_account": "5000 - Aufwendungen f. Roh-, Hilfs- und Betriebsstoffe und f. bezogene Waren - B",
                "cost_center": "Main - B"
            }],
            "taxes": [{
                "charge_type": pr['taxes'][0]['charge_type'],
                "account_head": pr['taxes'][0]['account_head'],
                "description": pr['taxes'][0]['description'],
                "rate": float(pr['taxes'][0]['rate']),
                "tax_amount": float(pr['taxes'][0]['tax_amount']),
                "total": float(pr['taxes'][0]['total']),
                "cost_center": "Main - B"
            }],
            "status": "Draft",
            "docstatus": 1,
            "is_opening": "No"
        }

    def generate_and_upload(self) -> List[Dict]:
        """Generate and upload purchase invoices in batch"""
        if not all([self.start_date, self.end_date, self.purchase_receipts]):
            raise ValueError("Generator not configured. Call configure() first.")

        self.successful_invoices = []  # Reset successful invoices
        try:
            if not self.purchase_receipts:
                raise ValueError("No purchase receipts provided to process")

            # Generate and upload invoices
            for i, pr in enumerate(self.purchase_receipts, 1):
                try:
                    invoice_date = self.calculate_invoice_date(pr['posting_date'])
                    invoice_doc = self.create_purchase_invoice(pr, invoice_date)

                    response = self.api.create(invoice_doc)

                    if response and 'data' in response:
                        content = response['data']
                        if 'name' in content:
                            invoice_doc['name'] = content['name']
                            invoice_doc['api_response'] = content  # Store complete API response
                            invoice_doc['purchase_receipt_reference'] = pr['name']  # Store reference to PR
                            if 'items' in content:
                                for idx, item in enumerate(invoice_doc['items']):
                                    item['name'] = content['items'][idx]['name']
                            self.successful_invoices.append(invoice_doc)
                            self.logger.info(
                                f"Successfully created PI {content['name']} ({i}/{len(self.purchase_receipts)})")

                except Exception as e:
                    self.logger.error(f"Error processing invoice {i}: {str(e)}")
                    continue

            self.logger.info(f"Completed batch with {len(self.successful_invoices)} successful uploads "
                             f"out of {len(self.purchase_receipts)} attempts")
            return self.successful_invoices

        except Exception as e:
            self.logger.error(f"Batch processing error: {str(e)}")
            raise

    def get_successful_invoices(self) -> List[Dict]:
        """Return the list of successful invoices for next process step"""
        return self.successful_invoices

    def save_to_csv(self, filename: str = 'batch_purchase_invoices.csv'):
        """Save batch results to CSV"""
        if not self.successful_invoices:
            self.logger.warning("No data to save to CSV.")
            return

        try:
            output_path = OUTPUT_DIR / filename

            rows = []
            for pi in self.successful_invoices:
                for item in pi['items']:
                    row = {
                        "ID": pi['name'],
                        "Credit To": pi['credit_to'],
                        "Date": pi['posting_date'],
                        "Due Date": pi['due_date'],
                        "Series": pi['naming_series'],
                        "Supplier": pi['supplier'],
                        "Item (Items)": item['item_code'],
                        "Accepted Qty (Items)": item['qty'],
                        "Accepted Qty in Stock UOM (Items)": f"{float(item['qty']) * float(item['conversion_factor']):.2f}".replace(
                            '.', ','),
                        "Amount (Items)": item['amount'],
                        "Amount (Company Currency) (Items)": item['base_amount'],
                        "Item Name (Items)": item['item_name'],
                        "Rate (Items)": item['rate'],
                        "Rate (Company Currency) (Items)": item['base_rate'],
                        "UOM (Items)": item['uom'],
                        "UOM Conversion Factor (Items)": item['conversion_factor'],
                        "Purchase Order (Items)": item['purchase_order'],
                        "Purchase Order Item (Items)": item['po_detail'],
                        "Purchase Receipt (Items)": item['purchase_receipt'],
                        "Purchase Receipt Detail (Items)": item['pr_detail'],
                        "ID (Purchase Taxes and Charges)": f"PITAX-{pi['name']}",
                        "Account Head (Purchase Taxes and Charges)": pi['taxes'][0]['account_head'],
                        "Add or Deduct (Purchase Taxes and Charges)": "Add",
                        "Consider Tax or Charge for (Purchase Taxes and Charges)": "Total",
                        "Description (Purchase Taxes and Charges)": pi['taxes'][0]['description'],
                        "Type (Purchase Taxes and Charges)": pi['taxes'][0]['charge_type'],
                        "Expense Head (Items)": item['expense_account'],
                        "Deferred Expense Account (Items)": item['expense_account']
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
            self.logger.info(f"Starting batch purchase invoice process for period: "
                             f"{self.start_date.date()} to {self.end_date.date()}")

            # Generate and upload invoices
            self.generate_and_upload()

            # Save results if any successful uploads
            if self.successful_invoices:
                self.save_to_csv()
                return True
            else:
                self.logger.warning("No successful invoices to save.")
                return False

        except Exception as e:
            self.logger.error(f"Batch process failed: {str(e)}")
            return False