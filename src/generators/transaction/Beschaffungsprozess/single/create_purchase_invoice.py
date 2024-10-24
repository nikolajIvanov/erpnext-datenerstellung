import csv
import os
from datetime import datetime, timedelta
import json
import logging
from typing import List, Dict, Tuple
from src.api.endpoints.purchase_invoice_api import PurchaseInvoiceAPI


class Config:
    BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    INPUT_DIR = os.path.join(BASE_DIR, 'generated')
    OUTPUT_DIR = os.path.join(BASE_DIR, 'generated')
    LOG_DIR = os.path.join(BASE_DIR, 'process_logs', 'purchase_invoices')
    API_PAYLOAD_DIR = os.path.join(BASE_DIR, 'api_payloads', 'purchase_invoices')
    INVOICE_DELAY = (0, 3)  # Invoice 0-3 days after receipt


# Ensure directories exist
os.makedirs(Config.LOG_DIR, exist_ok=True)
os.makedirs(Config.API_PAYLOAD_DIR, exist_ok=True)

# Configure file logger
file_logger = logging.getLogger('file_logger')
file_logger.setLevel(logging.INFO)
file_handler = logging.FileHandler(
    os.path.join(Config.LOG_DIR, f'purchase_invoice_{datetime.now().strftime("%Y%m%d_%H%M%S")}.log')
)
file_handler.setFormatter(logging.Formatter('%(message)s'))
file_logger.addHandler(file_handler)

# Configure console logger
console_logger = logging.getLogger('console_logger')
console_logger.setLevel(logging.INFO)
console_handler = logging.StreamHandler()
console_handler.setFormatter(logging.Formatter('%(message)s'))
console_logger.addHandler(console_handler)

# Prevent loggers from propagating to root logger
file_logger.propagate = False
console_logger.propagate = False


def load_purchase_receipts() -> List[Dict]:
    with open(os.path.join(Config.INPUT_DIR, 'purchase_receipts.csv'), 'r', encoding='utf-8') as f:
        return list(csv.DictReader(f))


def generate_purchase_invoices(purchase_receipts: List[Dict]) -> List[Dict]:
    purchase_invoices = []
    for pr in purchase_receipts:
        try:
            # Parse the receipt date and validate it's not None
            receipt_date = datetime.strptime(pr['Date'], "%Y-%m-%d")
            logging.info(f"Processing purchase receipt from date: {receipt_date}")

            # Calculate posting date and due date relative to receipt date
            posting_date = receipt_date  # Same day as receipt
            due_date = posting_date + timedelta(days=30)  # Standard 30 days payment term

            # Parse and convert amounts
            received_qty = float(
                pr['Received Quantity (Items)'].replace(',', '.') if isinstance(pr['Received Quantity (Items)'],
                                                                                str) else pr[
                    'Received Quantity (Items)'])
            rate = float(pr['Rate (Company Currency) (Items)'].replace(',', '.') if isinstance(
                pr['Rate (Company Currency) (Items)'], str) else pr['Rate (Company Currency) (Items)'])
            amount = round(received_qty * rate, 2)
            tax_rate = float(pr['Tax Rate (Purchase Taxes and Charges)'])
            tax_amount = round(amount * (tax_rate / 100), 2)
            grand_total = amount + tax_amount

            api_invoice = {
                "doctype": "Purchase Invoice",
                "naming_series": "ACC-PINV-.YYYY.-",
                "company": pr['Company'],
                "posting_date": posting_date.strftime("%Y-%m-%d"),
                "posting_time": "00:00:00",
                "due_date": due_date.strftime("%Y-%m-%d"),
                "bill_date": posting_date.strftime("%Y-%m-%d"),
                "bill_no": f"BILL-{pr['ID']}",
                "supplier": pr['Supplier'],
                "currency": "EUR",
                "conversion_rate": 1.0,
                "buying_price_list": "Standard Buying",
                "price_list_currency": "EUR",
                "plc_conversion_rate": 1.0,
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
                    "description": f"Receipt for {pr['Item Name (Items)']}",
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
                    "purchase_order": pr['Purchase Order (Items)'],  # Add PO reference
                    "po_detail": pr['Purchase Order Item (Items)'],  # Add PO item reference
                    "purchase_receipt": pr['ID'],  # Add PR reference
                    "pr_detail": pr['ID (Items)'],  # Add PR item reference
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
            purchase_invoices.append(api_invoice)

        except Exception as e:
            logging.error(f"Error generating purchase invoice for receipt {pr.get('ID', 'unknown')}: {str(e)}")
            continue

    return purchase_invoices


def save_api_payload(payload: Dict, identifier: str) -> str:
    """Save API payload to JSON file with timestamp"""
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"purchase_invoice_{identifier}_{timestamp}.json"
    filepath = os.path.join(Config.API_PAYLOAD_DIR, filename)

    with open(filepath, 'w', encoding='utf-8') as f:
        json.dump(payload, f, indent=2, ensure_ascii=False)

    file_logger.info(f"Saved purchase invoice payload to {filepath}")
    return filepath


def upload_purchase_invoice_to_api(purchase_invoice: Dict) -> Tuple[bool, str, Dict]:
    api = PurchaseInvoiceAPI()
    try:
        response = api.create(purchase_invoice)
        content = response['data']

        if 'name' in content:
            system_id = content['name']
            logging.info(f"Successfully uploaded Purchase Invoice. ID: {system_id}")
            return True, system_id, content
        else:
            raise ValueError("API response did not contain expected data structure")
    except Exception as e:
        logging.error(f"Failed to upload Purchase Invoice: {str(e)}")
        return False, "", {}


def save_to_csv(uploaded_data: List[Dict], original_data: Dict[str, Dict], filename: str):
    if not uploaded_data:
        logging.warning("No data to save to CSV.")
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

    flat_data = []
    for uploaded_pi in uploaded_data:
        pi_id = uploaded_pi.get('name')
        if pi_id not in original_data:
            logging.warning(f"No original data found for uploaded PI: {pi_id}")
            continue

        original_pi = original_data[pi_id]

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
                "Accepted Qty in Stock UOM (Items)": f"{original_pi['items'][0]['stock_qty']:.2f}".replace('.', ','),
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
            flat_data.append(row)
        except KeyError as e:
            logging.error(f"Missing key while flattening data for PI {pi_id}: {str(e)}")
            continue
        except Exception as e:
            logging.error(f"Error processing PI {pi_id}: {str(e)}")
            continue

    try:
        with open(os.path.join(Config.OUTPUT_DIR, filename), 'w', newline='', encoding='utf-8') as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(flat_data)
        logging.info(f"Successfully saved {len(flat_data)} records to {filename}")
    except Exception as e:
        logging.error(f"Error saving to CSV: {str(e)}")


def main():
    purchase_receipts = load_purchase_receipts()
    logging.info(f"Loaded {len(purchase_receipts)} purchase receipts")

    purchase_invoices = generate_purchase_invoices(purchase_receipts)
    logging.info(f"Generated {len(purchase_invoices)} purchase invoices")

    successful_uploads = []
    original_data = {}  # Store original data with generated IDs

    for pi in purchase_invoices:
        success, system_id, response_data = upload_purchase_invoice_to_api(pi)
        if success:
            # Store original data with the system-generated ID
            original_data[system_id] = pi

            # Add system-generated ID to the response
            response_data['name'] = system_id
            successful_uploads.append(response_data)

    # Save to CSV using original data
    save_to_csv(successful_uploads, original_data, 'purchase_invoices.csv')
    logging.info(f"Successfully uploaded {len(successful_uploads)} out of {len(purchase_invoices)} purchase invoices")


if __name__ == "__main__":
    main()
