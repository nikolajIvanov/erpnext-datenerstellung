import csv
import random
from datetime import datetime, timedelta
from typing import List, Dict, Tuple
from src.api.endpoints.purchase_invoice_api import PurchaseInvoiceAPI
from src.core.base_transaction import BaseConfig
from src.core.logging import ProcessLogger
from src.config.settings import (
    COMPANY, CURRENCY, CONVERSION_RATE,
    MASTER_DATA_DIR, OUTPUT_DIR
)


class PurchaseInvoiceConfig(BaseConfig):
    """Configuration specific to purchase invoice process."""

    def __init__(self):
        super().__init__('purchase_invoice')

        # Process-specific settings
        self.INVOICE_DELAY = (0, 3)  # Invoice 0-3 days after receipt


class PurchaseInvoiceGenerator:
    def __init__(self):
        self.config = PurchaseInvoiceConfig()
        self.logger = ProcessLogger(self.config)
        self.api = PurchaseInvoiceAPI()
        self.original_data = {}  # Store original data with generated IDs

    def upload_purchase_invoice_to_api(self, purchase_invoice: Dict) -> Tuple[bool, str, Dict]:
        """Upload purchase invoice to API with improved error handling."""
        try:
            response = self.api.create(purchase_invoice)

            if not response or 'data' not in response:
                return False, "", {}

            content = response['data']

            if isinstance(content, dict) and 'name' in content:
                system_id = content['name']
                self.original_data[system_id] = purchase_invoice  # Store original data
                self.logger.log_info(f"Successfully created Purchase Invoice with ID: {system_id}")
                return True, system_id, content

            return False, "", {}

        except Exception as e:
            self.logger.log_error(f"Failed to upload Purchase Invoice: {str(e)}")
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

    def generate_purchase_invoices(self, purchase_receipts: List[Dict]) -> List[Dict]:
        """Generate purchase invoice documents."""
        purchase_invoices = []
        for pr in purchase_receipts:
            try:
                receipt_date = datetime.strptime(pr['Date'], "%Y-%m-%d")
                self.logger.log_info(f"Processing purchase receipt from date: {receipt_date}")

                # Calculate posting date and due date
                posting_date = receipt_date + timedelta(days=random.randint(*self.config.INVOICE_DELAY))
                due_date = posting_date + timedelta(days=30)  # Standard 30 days payment term

                # Parse and convert amounts
                received_qty = float(pr['Received Quantity (Items)'].replace(',', '.')
                                     if isinstance(pr['Received Quantity (Items)'], str)
                                     else pr['Received Quantity (Items)'])
                rate = float(pr['Rate (Company Currency) (Items)'].replace(',', '.')
                             if isinstance(pr['Rate (Company Currency) (Items)'], str)
                             else pr['Rate (Company Currency) (Items)'])
                amount = round(received_qty * rate, 2)
                tax_rate = float(pr['Tax Rate (Purchase Taxes and Charges)'])
                tax_amount = round(amount * (tax_rate / 100), 2)
                grand_total = amount + tax_amount

                invoice = {
                    "doctype": "Purchase Invoice",
                    "naming_series": "ACC-PINV-.YYYY.-",
                    "company": COMPANY,
                    "posting_date": posting_date.strftime("%Y-%m-%d"),
                    "posting_time": datetime.now().strftime("%H:%M:%S"),
                    "due_date": due_date.strftime("%Y-%m-%d"),
                    "bill_date": posting_date.strftime("%Y-%m-%d"),
                    "bill_no": f"BILL-{pr['ID']}",
                    "supplier": pr['Supplier'],
                    "currency": CURRENCY,
                    "conversion_rate": CONVERSION_RATE,
                    "buying_price_list": "Standard Buying",
                    "price_list_currency": CURRENCY,
                    "plc_conversion_rate": CONVERSION_RATE,
                    "is_return": 0,
                    "update_stock": 0,
                    "total_qty": received_qty,
                    "base_total": amount,
                    "base_net_total": amount,
                    "total": amount,
                    "net_total": amount,
                    "base_grand_total": grand_total,
                    "grand_total": grand_total,
                    "docstatus": 1,
                    "credit_to": "3500 - Sonstige Verb. - B",
                    "is_opening": "No",

                    "items": [{
                        "item_code": pr['Item Code (Items)'],
                        "item_name": pr['Item Name (Items)'],
                        "description": f"Invoice for {pr['Item Name (Items)']}",
                        "received_qty": received_qty,
                        "qty": received_qty,
                        "stock_qty": received_qty,
                        "uom": pr['UOM (Items)'],
                        "stock_uom": pr['Stock UOM (Items)'],
                        "conversion_factor": float(pr['Conversion Factor (Items)']),
                        "rate": rate,
                        "amount": amount,
                        "base_rate": rate,
                        "base_amount": amount,
                        "warehouse": pr['Accepted Warehouse (Items)'],
                        "purchase_order": pr['Purchase Order (Items)'],
                        "po_detail": pr['Purchase Order Item (Items)'],
                        "purchase_receipt": pr['ID'],
                        "pr_detail": pr['ID (Items)'],
                        "batch_no": pr.get('Batch No (Items)', ''),
                        "expense_account": "5000 - Aufwendungen f. Roh-, Hilfs- und Betriebsstoffe und f. bezogene Waren - B",
                        "cost_center": "Main - B"
                    }],

                    "taxes": [{
                        "charge_type": pr['Type (Purchase Taxes and Charges)'],
                        "account_head": pr['Account Head (Purchase Taxes and Charges)'],
                        "description": pr['Description (Purchase Taxes and Charges)'],
                        "rate": tax_rate,
                        "tax_amount": tax_amount,
                        "total": grand_total,
                        "base_tax_amount": tax_amount,
                        "base_total": grand_total,
                        "category": "Total",
                        "add_deduct_tax": "Add",
                        "included_in_print_rate": 0,
                        "cost_center": "Main - B"
                    }]
                }
                purchase_invoices.append(invoice)

            except Exception as e:
                self.logger.log_error(
                    f"Error generating purchase invoice for receipt {pr.get('ID', 'unknown')}: {str(e)}")
                continue

        return purchase_invoices

    def save_to_csv(self, data: List[Dict], filename: str):
        """Save purchase invoices to CSV file."""
        if not data:
            self.logger.log_warning("No data to save to CSV.")
            return

        fieldnames = [
            "ID", "Credit To", "Date", "Due Date", "Series", "Supplier",
            "Item (Items)", "Accepted Qty (Items)", "Accepted Qty in Stock UOM (Items)",
            "Amount (Items)", "Amount (Company Currency) (Items)",
            "Item Name (Items)", "Rate (Items)", "Rate (Company Currency) (Items)",
            "UOM (Items)", "UOM Conversion Factor (Items)",
            "Purchase Order (Items)", "Purchase Order Item (Items)",
            "Purchase Receipt (Items)", "Purchase Receipt Detail (Items)",
            "ID (Purchase Taxes and Charges)",
            "Account Head (Purchase Taxes and Charges)",
            "Add or Deduct (Purchase Taxes and Charges)",
            "Consider Tax or Charge for (Purchase Taxes and Charges)",
            "Description (Purchase Taxes and Charges)",
            "Type (Purchase Taxes and Charges)",
            "Expense Head (Items)",
            "Deferred Expense Account (Items)"
        ]

        try:
            flattened_data = []
            for uploaded_pi in data:
                pi_id = uploaded_pi.get('name')
                original_pi = self.original_data.get(pi_id)

                if not original_pi:
                    self.logger.log_warning(f"No original data found for uploaded PI: {pi_id}")
                    continue

                try:
                    row = {
                        "ID": pi_id,
                        "Credit To": original_pi["credit_to"],
                        "Date": original_pi["posting_date"],
                        "Due Date": original_pi["due_date"],
                        "Series": original_pi["naming_series"],
                        "Supplier": original_pi["supplier"],
                        "Item (Items)": original_pi["items"][0]["item_code"],
                        "Accepted Qty (Items)": original_pi["items"][0]["qty"],
                        "Accepted Qty in Stock UOM (Items)": f"{original_pi['items'][0]['stock_qty']:.2f}".replace('.',
                                                                                                                   ','),
                        "Amount (Items)": original_pi["items"][0]["amount"],
                        "Amount (Company Currency) (Items)": original_pi["items"][0]["base_amount"],
                        "Item Name (Items)": original_pi["items"][0]["item_name"],
                        "Rate (Items)": original_pi["items"][0]["rate"],
                        "Rate (Company Currency) (Items)": original_pi["items"][0]["base_rate"],
                        "UOM (Items)": original_pi["items"][0]["uom"],
                        "UOM Conversion Factor (Items)": original_pi["items"][0]["conversion_factor"],
                        "Purchase Order (Items)": original_pi["items"][0].get("purchase_order", ""),
                        "Purchase Order Item (Items)": original_pi["items"][0].get("po_detail", ""),
                        "Purchase Receipt (Items)": original_pi["items"][0]["purchase_receipt"],
                        "Purchase Receipt Detail (Items)": original_pi["items"][0]["pr_detail"],
                        "Expense Head (Items)": original_pi["items"][0]["expense_account"],
                        "Deferred Expense Account (Items)": original_pi["items"][0]["expense_account"],
                        "Account Head (Purchase Taxes and Charges)": original_pi["taxes"][0]["account_head"],
                        "Add or Deduct (Purchase Taxes and Charges)": original_pi["taxes"][0]["add_deduct_tax"],
                        "Consider Tax or Charge for (Purchase Taxes and Charges)": "Total",
                        "Description (Purchase Taxes and Charges)": original_pi["taxes"][0]["description"],
                        "Type (Purchase Taxes and Charges)": original_pi["taxes"][0]["charge_type"],
                        "ID (Purchase Taxes and Charges)": f"PITAX-{pi_id}"
                    }
                    flattened_data.append(row)
                except KeyError as e:
                    self.logger.log_error(f"Missing key while flattening data for PI {pi_id}: {str(e)}")
                    continue
                except Exception as e:
                    self.logger.log_error(f"Error processing PI {pi_id}: {str(e)}")
                    continue

            output_path = OUTPUT_DIR / filename

            with open(output_path, 'w', newline='', encoding='utf-8') as f:
                writer = csv.DictWriter(f, fieldnames=fieldnames)
                writer.writeheader()
                writer.writerows(flattened_data)

            self.logger.log_info(f"Successfully saved {len(flattened_data)} records to {filename}")

        except Exception as e:
            self.logger.log_error(f"Error saving to CSV: {str(e)}")
            raise

    def process(self):
        """Main process for generating and uploading purchase invoices."""
        try:
            # Load and prepare data
            purchase_receipts = self.load_csv_data('purchase_receipts.csv')
            self.logger.log_info(f"Loaded {len(purchase_receipts)} purchase receipts")

            # Generate purchase invoices
            purchase_invoices = self.generate_purchase_invoices(purchase_receipts)
            self.logger.log_info(f"Generated {len(purchase_invoices)} purchase invoices")

            # Upload and track successful uploads
            successful_uploads = []
            for pi in purchase_invoices:
                success, system_id, response_data = self.upload_purchase_invoice_to_api(pi)
                if success:
                    response_data['name'] = system_id
                    successful_uploads.append(response_data)

            # Save results
            if successful_uploads:
                self.save_to_csv(successful_uploads, 'purchase_invoices.csv')
            else:
                self.logger.log_warning("No successful uploads to save to CSV.")

        except Exception as e:
            self.logger.log_error(f"Process Error: {str(e)}")
            raise


def main():
    generator = PurchaseInvoiceGenerator()
    generator.process()


if __name__ == "__main__":
    main()