import csv
import os
from datetime import datetime, timedelta
import json
import random
import logging
from typing import List, Dict, Tuple
from api.purchase_invoice_api import PurchaseInvoiceAPI


class Config:
    BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    INPUT_DIR = os.path.join(BASE_DIR, 'Generated_CSV')
    OUTPUT_DIR = os.path.join(BASE_DIR, 'Generated_CSV')
    LOG_DIR = os.path.join(BASE_DIR, 'logs', 'purchase_invoices')
    JSON_DIR = os.path.join(BASE_DIR, 'api_payloads', 'purchase_invoices')
    INVOICE_DELAY = (0, 3)  # Invoice 0-3 days after receipt


# Ensure directories exist
os.makedirs(Config.LOG_DIR, exist_ok=True)
os.makedirs(Config.JSON_DIR, exist_ok=True)

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
        pr_date = datetime.strptime(pr['Date'], "%Y-%m-%d")
        pi_date = pr_date + timedelta(days=random.randint(*Config.INVOICE_DELAY))
        due_date = pi_date + timedelta(days=random.choice([0, 30, 60]))

        # Convert quantities and amounts
        received_qty = float(pr['Received Quantity (Items)'].replace(',', '.'))
        conversion_factor = float(pr['Conversion Factor (Items)'].replace(',', '.'))
        rate = float(pr['Rate (Company Currency) (Items)'])
        amount = received_qty * rate
        tax_rate = float(pr['Tax Rate (Purchase Taxes and Charges)'])
        tax_amount = amount * (tax_rate / 100)
        grand_total = amount + tax_amount

        api_invoice = {
            "doctype": "Purchase Invoice",
            "naming_series": "ACC-PINV-.YYYY.-",
            "company": pr['Company'],
            "posting_date": pi_date.strftime("%Y-%m-%d"),
            "posting_time": datetime.now().strftime("%H:%M:%S"),
            "due_date": due_date.strftime("%Y-%m-%d"),
            "supplier": pr['Supplier'],
            "currency": "EUR",
            "conversion_rate": 1.0,
            "buying_price_list": "Standard Buying",
            "price_list_currency": "EUR",
            "plc_conversion_rate": 1.0,
            "ignore_pricing_rule": 0,
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
            "party_account_currency": "EUR",
            "is_opening": "No",
            "against_expense_account": "70001 - Wareneingangs-­Verrechnungskonto - B",
            "items": [{
                "item_code": pr['Item Code (Items)'],
                "item_name": pr['Item Name (Items)'],
                "description": f"Receipt for {pr['Item Name (Items)']}",
                "received_qty": received_qty,
                "qty": received_qty,
                "stock_qty": received_qty * conversion_factor,
                "uom": pr['UOM (Items)'],
                "stock_uom": pr['Stock UOM (Items)'],
                "conversion_factor": conversion_factor,
                "rate": rate,
                "amount": amount,
                "base_rate": rate,
                "base_amount": amount,
                "warehouse": pr['Accepted Warehouse (Items)'],
                "purchase_receipt": pr['ID'],
                "pr_detail": pr['ID (Items)'],
                "purchase_order": pr['Purchase Order (Items)'],
                "po_detail": pr['Purchase Order Item (Items)'],
                "expense_account": "70001 - Wareneingangs-­Verrechnungskonto - B",
                "cost_center": "Main - B",
                "batch_no": pr['Batch No (Items)']
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
    return purchase_invoices


def save_api_payload(payload: Dict, identifier: str) -> str:
    """Save API payload to JSON file with timestamp"""
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"purchase_invoice_{identifier}_{timestamp}.json"
    filepath = os.path.join(Config.JSON_DIR, filename)

    with open(filepath, 'w', encoding='utf-8') as f:
        json.dump(payload, f, indent=2, ensure_ascii=False)

    file_logger.info(f"Saved purchase invoice payload to {filepath}")
    return filepath


def upload_purchase_invoice_to_api(purchase_invoice: Dict) -> Tuple[bool, str, Dict]:
    api = PurchaseInvoiceAPI()
    try:
        # Save payload before sending
        identifier = purchase_invoice.get('supplier', 'unknown')
        filepath = save_api_payload(purchase_invoice, identifier)

        response = api.create(purchase_invoice)
        content = response['data']

        if 'name' in content:
            system_id = content['name']
            console_logger.info(f"Successfully uploaded Purchase Invoice. ID: {system_id}")
            file_logger.info(f"Successfully created Purchase Invoice with ID: {system_id}")
            return True, system_id, content
        else:
            file_logger.error(f"API response did not contain expected data structure. Payload saved at: {filepath}")
            raise ValueError("API response did not contain expected data structure")
    except Exception as e:
        file_logger.error(f"Failed to upload Purchase Invoice: {str(e)}")
        return False, "", {}


def save_to_csv(data: List[Dict], filename: str):
    if not data:
        file_logger.warning("No data to save to CSV.")
        return

    fieldnames = [
        "ID", "Credit To", "Date", "Due Date", "Series", "Supplier", "Item (Items)",
        "Accepted Qty (Items)", "Accepted Qty in Stock UOM (Items)",
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
        "Type (Purchase Taxes and Charges)", "Expense Head (Items)",
        "Deferred Expense Account (Items)"
    ]

    with open(os.path.join(Config.OUTPUT_DIR, filename), 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(data)


def main():
    purchase_receipts = load_purchase_receipts()
    console_logger.info(f"Loaded {len(purchase_receipts)} purchase receipts")

    purchase_invoices = generate_purchase_invoices(purchase_receipts)
    console_logger.info(f"Generated {len(purchase_invoices)} purchase invoices")

    successful_uploads = []
    for pi in purchase_invoices:
        success, system_id, response_data = upload_purchase_invoice_to_api(pi)
        if success:
            # Prepare data for CSV
            csv_data = {
                "ID": system_id,
                "Credit To": pi['credit_to'],
                "Date": pi['posting_date'],
                "Due Date": pi['due_date'],
                "Series": pi['naming_series'],
                "Supplier": pi['supplier'],
                "Item (Items)": pi['items'][0]['item_code'],
                "Accepted Qty (Items)": pi['items'][0]['received_qty'],
                "Accepted Qty in Stock UOM (Items)": f"{pi['items'][0]['stock_qty']:.2f}".replace('.', ','),
                "Amount (Items)": pi['items'][0]['amount'],
                "Amount (Company Currency) (Items)": pi['items'][0]['base_amount'],
                "Item Name (Items)": pi['items'][0]['item_name'],
                "Rate (Items)": pi['items'][0]['rate'],
                "Rate (Company Currency) (Items)": pi['items'][0]['base_rate'],
                "UOM (Items)": pi['items'][0]['uom'],
                "UOM Conversion Factor (Items)": pi['items'][0]['conversion_factor'],
                "Purchase Order (Items)": pi['items'][0]['purchase_order'],
                "Purchase Order Item (Items)": pi['items'][0]['po_detail'],
                "Purchase Receipt (Items)": pi['items'][0]['purchase_receipt'],
                "Purchase Receipt Detail (Items)": pi['items'][0]['pr_detail'],
                "ID (Purchase Taxes and Charges)": response_data['taxes'][0]['name'] if 'taxes' in response_data else '',
                "Account Head (Purchase Taxes and Charges)": pi['taxes'][0]['account_head'],
                "Add or Deduct (Purchase Taxes and Charges)": pi['taxes'][0]['add_deduct_tax'],
                "Consider Tax or Charge for (Purchase Taxes and Charges)": "Total",
                "Description (Purchase Taxes and Charges)": pi['taxes'][0]['description'],
                "Type (Purchase Taxes and Charges)": pi['taxes'][0]['charge_type'],
                "Expense Head (Items)": pi['items'][0]['expense_account'],
                "Deferred Expense Account (Items)": pi['items'][0]['expense_account']
            }
            successful_uploads.append(csv_data)

    save_to_csv(successful_uploads, 'purchase_invoices.csv')
    console_logger.info(f"Successfully uploaded {len(successful_uploads)} out of {len(purchase_invoices)} purchase invoices")


if __name__ == "__main__":
    main()