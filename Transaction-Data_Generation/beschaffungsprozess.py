import csv
from datetime import datetime, timedelta
import random
import os


class Config:
    BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    INPUT_DIR = os.path.join(BASE_DIR, 'Master-Data_Processed_CSV')
    OUTPUT_DIR = os.path.join(BASE_DIR, 'Generated_CSV')
    START_DATE = datetime(2023, 1, 1)
    END_DATE = datetime(2023, 12, 31)
    NUM_ORDERS = 2
    PAYMENT_TERMS = [0, 30, 60]
    TARGET_WAREHOUSE = "Lager Stuttgart - B"
    MAPPING_FILE = 'item_supplier_mapping.csv'


def load_csv_data(filename):
    with open(os.path.join(Config.INPUT_DIR, filename), 'r', encoding='utf-8') as f:
        return list(csv.DictReader(f))


def load_item_supplier_mapping():
    mapping = {}
    mapping_file = os.path.join(Config.INPUT_DIR, Config.MAPPING_FILE)
    if os.path.exists(mapping_file):
        with open(mapping_file, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row in reader:
                mapping[row['Item Code']] = row['Supplier ID']
    return mapping


def generate_id(prefix, date):
    year = date.year
    number = random.randint(1, 99999)
    return f"{prefix}-{year}-{number:05d}"


def random_date(start_date, end_date):
    return start_date + timedelta(
        seconds=random.randint(0, int((end_date - start_date).total_seconds()))
    )


def load_item_batch_info(items):
    return {item['Item Code']: item.get('Has Batch No', '0') == '1' for item in items}


def load_batch_numbers(filename):
    batch_numbers = {}
    with open(os.path.join(Config.INPUT_DIR, filename), 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            batch_numbers[row['Item']] = row['Batch ID']
    return batch_numbers


def generate_purchase_orders(products, item_supplier_mapping):
    purchase_orders = []
    for _ in range(Config.NUM_ORDERS):
        po_date = random_date(Config.START_DATE, Config.END_DATE)
        product = random.choice(products)
        item_code = product['Item Code']

        supplier_id = item_supplier_mapping.get(item_code, "DEFAULT_SUPPLIER_ID")

        quantity = random.randint(1, 100)
        rate = float(product['Valuation Rate'])
        amount = round(quantity * rate, 2)

        po = {
            "ID": generate_id("PUR-ORD", po_date),
            "Company": "Velo GmbH",
            "Currency": "EUR",
            "Date": po_date.strftime("%Y-%m-%d"),
            "Exchange Rate": "1,00",
            "Series": "PUR-ORD-.YYYY.-",
            "Status": "To Receive and Bill",
            "Supplier": supplier_id,
            "Title": f"Purchase Order for {supplier_id}",
            "ID (Items)": generate_id("POITEM", po_date),
            "Amount (Items)": amount,
            "Item Code (Items)": item_code,
            "Item Name (Items)": product['Item Name'],
            "Quantity (Items)": quantity,
            "Rate (Items)": rate,
            "Required By (Items)": (po_date + timedelta(days=7)).strftime("%Y-%m-%d"),
            "Stock UOM (Items)": product['Default Unit of Measure'],
            "UOM (Items)": product['Default Unit of Measure'],
            "UOM Conversion Factor (Items)": "1,00",
            "Set Target Warehouse": Config.TARGET_WAREHOUSE
        }
        purchase_orders.append(po)
    return purchase_orders


def generate_purchase_receipts(purchase_orders, item_batch_info, batch_numbers):
    purchase_receipts = []
    for po in purchase_orders:
        pr_date = datetime.strptime(po['Date'], "%Y-%m-%d") + timedelta(days=random.randint(1, 7))
        item_code = po['Item Code (Items)']
        batch_no = batch_numbers.get(item_code, "") if item_batch_info.get(item_code, False) else ""
        pr = {
            "ID": generate_id("MAT-PRE", pr_date),
            "Company": po['Company'],
            "Currency": po['Currency'],
            "Date": pr_date.strftime("%Y-%m-%d"),
            "Exchange Rate": "1,00",
            "Net Total (Company Currency)": po['Amount (Items)'],
            "Posting Time": pr_date.strftime("%H:%M:%S.%f"),
            "Series": "MAT-PRE-.YYYY.-",
            "Status": "Draft",
            "Supplier": po['Supplier'],
            "ID (Items)": generate_id("PRITEM", pr_date),
            "Conversion Factor (Items)": "1,00",
            "Item Code (Items)": po['Item Code (Items)'],
            "Item Name (Items)": po['Item Name (Items)'],
            "Rate (Company Currency) (Items)": po['Rate (Items)'],
            "Received Quantity (Items)": po['Quantity (Items)'],
            "Stock UOM (Items)": po['Stock UOM (Items)'],
            "UOM (Items)": po['UOM (Items)'],
            "Purchase Order (Items)": po['ID'],
            "Purchase Order Item (Items)": po['ID (Items)'],
            "Accepted Warehouse (Items)": Config.TARGET_WAREHOUSE,
            "Tax Rate (Purchase Taxes and Charges)": 19.00,
            "Account Head (Purchase Taxes and Charges)": "1406 - Abziehbare Vorsteuer 19 % - B",
            "Accepted Quantity (Items)": po['Quantity (Items)'],
            "Description (Purchase Taxes and Charges)": "Abziehbare Vorsteuer 19 %",
            "Type (Purchase Taxes and Charges)": "On Net Total",
            "Add or Deduct (Purchase Taxes and Charges)": "Add",
            "Consider Tax or Charge for (Purchase Taxes and Charges)": "Total",
            "Batch No (Items)": batch_no
        }
        purchase_receipts.append(pr)
    return purchase_receipts


def generate_purchase_invoices(purchase_receipts):
    purchase_invoices = []
    for pr in purchase_receipts:
        pi_date = datetime.strptime(pr['Date'], "%Y-%m-%d") + timedelta(days=random.randint(0, 3))

        # Überprüfe den Typ und konvertiere entsprechend
        received_quantity = pr['Received Quantity (Items)'] if isinstance(pr['Received Quantity (Items)'], (int, float)) else float(pr['Received Quantity (Items)'].replace(',', '.'))
        conversion_factor = float(pr['Conversion Factor (Items)'].replace(',', '.')) if isinstance(pr['Conversion Factor (Items)'], str) else pr['Conversion Factor (Items)']
        accepted_qty_in_stock_uom = received_quantity * conversion_factor
        due_date = pi_date + timedelta(days=random.choice([0, 30, 60]))  # Zahlungsziel: sofort, 30 oder 60 Tage

        pi = {
            "ID": generate_id("ACC-PINV", pi_date),
            "Credit To": "3500 - Sonstige Verb. - B",
            "Date": pi_date.strftime("%Y-%m-%d"),
            "Due Date": due_date.strftime("%Y-%m-%d"),
            "Series": "ACC-PINV-.YYYY.-",
            "Supplier": pr['Supplier'],
            "Item (Items)": pr['Item Code (Items)'],
            "Accepted Qty (Items)": pr['Received Quantity (Items)'],
            "Accepted Qty in Stock UOM (Items)": f"{accepted_qty_in_stock_uom:.2f}".replace('.', ','),
            "Amount (Items)": pr['Net Total (Company Currency)'],
            "Amount (Company Currency) (Items)": pr['Net Total (Company Currency)'],
            "Item Name (Items)": pr['Item Name (Items)'],
            "Rate (Items)": pr['Rate (Company Currency) (Items)'],
            "Rate (Company Currency) (Items)": pr['Rate (Company Currency) (Items)'],
            "UOM (Items)": pr['UOM (Items)'],
            "UOM Conversion Factor (Items)": pr['Conversion Factor (Items)'],
            "Purchase Order (Items)": pr['Purchase Order (Items)'],
            "Purchase Order Item (Items)": pr['Purchase Order Item (Items)'],
            "Purchase Receipt (Items)": pr['ID'],
            "Purchase Receipt Detail (Items)": pr['ID (Items)'],
            "ID (Purchase Taxes and Charges)": generate_id("PITAX", pi_date),
            "Account Head (Purchase Taxes and Charges)": pr['Account Head (Purchase Taxes and Charges)'],
            "Add or Deduct (Purchase Taxes and Charges)": pr['Add or Deduct (Purchase Taxes and Charges)'],
            "Consider Tax or Charge for (Purchase Taxes and Charges)": pr[
                'Consider Tax or Charge for (Purchase Taxes and Charges)'],
            "Description (Purchase Taxes and Charges)": pr['Description (Purchase Taxes and Charges)'],
            "Type (Purchase Taxes and Charges)": pr['Type (Purchase Taxes and Charges)'],
            "Expense Head (Items)": "5000 - Aufwendungen f. Roh-, Hilfs- und Betriebsstoffe und f. bezogene Waren - B",
            "Deferred Expense Account (Items)": "5000 - Aufwendungen f. Roh-, Hilfs- und Betriebsstoffe und f. bezogene Waren - B"

        }
        purchase_invoices.append(pi)
    return purchase_invoices


def generate_payment_entries(purchase_invoices):
    payment_entries = []
    for pi in purchase_invoices:
        payment_date = datetime.strptime(pi['Due Date'], "%Y-%m-%d")

        # Überprüfen Sie den Typ und konvertieren Sie entsprechend
        if isinstance(pi['Amount (Company Currency) (Items)'], str):
            amount = float(pi['Amount (Company Currency) (Items)'].replace(',', '.'))
        else:
            amount = float(pi['Amount (Company Currency) (Items)'])

        pe = {
            "ID": generate_id("ACC-PAY", payment_date),
            "Account Currency (From)": "EUR",
            "Account Currency (To)": "EUR",
            "Account Paid From": "1800 - Bank - B",
            "Account Paid To": "3500 - Sonstige Verb. - B",
            "Company": "Velo GmbH",
            "Paid Amount": f"{amount:.2f}".replace('.', ','),
            "Paid Amount (Company Currency)": f"{amount:.2f}".replace('.', ','),
            "Payment Type": "Pay",
            "Posting Date": payment_date.strftime("%Y-%m-%d"),
            "Received Amount": f"{amount:.2f}".replace('.', ','),
            "Received Amount (Company Currency)": f"{amount:.2f}".replace('.', ','),
            "Series": "ACC-PAY-.YYYY.-",
            "Source Exchange Rate": "1,00",
            "Target Exchange Rate": "1,00",
            "ID (Payment References)": generate_id("PAYREF", payment_date),
            "Type (Payment References)": "Purchase Invoice",
            "Name (Payment References)": pi['ID'],
            "ID (Advance Taxes and Charges)": generate_id("ADTAX", payment_date),
            "Account Head (Advance Taxes and Charges)": "1406 - Abziehbare Vorsteuer 19 % - B",
            "Add Or Deduct (Advance Taxes and Charges)": "Add",
            "Description (Advance Taxes and Charges)": "Abziehbare Vorsteuer 19 %",
            "Party Type": "Supplier",
            "Party": pi["Supplier"],
            "Cheque/Reference Date": payment_date.strftime("%Y-%m-%d"),
            "Cheque/Reference No": random.randint(1, 1000),
            "Type (Advance Taxes and Charges)": "Actual"
        }
        payment_entries.append(pe)
    return payment_entries


def save_to_csv(data, filename, fieldnames):
    with open(os.path.join(Config.OUTPUT_DIR, filename), 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames, extrasaction='ignore')
        writer.writeheader()
        writer.writerows(data)


def main():
    products = load_csv_data('items.csv')
    print(f"Loaded {len(products)} products")

    item_batch_info = load_item_batch_info(products)
    print(f"Loaded batch info for {len(item_batch_info)} items")

    item_supplier_mapping = load_item_supplier_mapping()
    print(f"Loaded supplier mapping for {len(item_supplier_mapping)} items")

    batch_numbers = load_batch_numbers('batch_numbers.csv')
    print(f"Loaded {len(batch_numbers)} batch numbers")

    purchase_orders = generate_purchase_orders(products, item_supplier_mapping)
    print(f"Generated {len(purchase_orders)} purchase orders")

    if not purchase_orders:
        print("No purchase orders generated. Check generate_purchase_orders function.")
        return

    purchase_receipts = generate_purchase_receipts(purchase_orders, item_batch_info, batch_numbers)
    print(f"Generated {len(purchase_receipts)} purchase receipts")

    if not purchase_receipts:
        print("No purchase receipts generated. Check generate_purchase_receipts function.")
        return

    purchase_invoices = generate_purchase_invoices(purchase_receipts)
    print(f"Generated {len(purchase_invoices)} purchase invoices")

    if not purchase_invoices:
        print("No purchase invoices generated. Check generate_purchase_invoices function.")
        return

    payment_entries = generate_payment_entries(purchase_invoices)
    print(f"Generated {len(payment_entries)} payment entries")

    save_to_csv(purchase_orders, 'purchase_orders.csv',
                ["ID", "Company", "Currency", "Date", "Exchange Rate", "Series", "Status", "Supplier", "Title",
                 "ID (Items)", "Amount (Items)", "Item Code (Items)", "Item Name (Items)",
                 "Quantity (Items)", "Rate (Items)", "Required By (Items)", "Stock UOM (Items)",
                 "UOM (Items)", "UOM Conversion Factor (Items)", "Set Target Warehouse"])

    save_to_csv(purchase_receipts, 'purchase_receipts.csv',
                ["ID", "Company", "Currency", "Date", "Exchange Rate", "Net Total (Company Currency)",
                 "Posting Time", "Series", "Status", "Supplier", "ID (Items)", "Conversion Factor (Items)",
                 "Item Code (Items)", "Item Name (Items)", "Rate (Company Currency) (Items)",
                 "Received Quantity (Items)", "Stock UOM (Items)", "UOM (Items)", "Purchase Order (Items)",
                 "Purchase Order Item (Items)", "Accepted Warehouse (Items)",
                 "Tax Rate (Purchase Taxes and Charges)", "Account Head (Purchase Taxes and Charges)",
                 "Accepted Quantity (Items)", "Description (Purchase Taxes and Charges)",
                 "Type (Purchase Taxes and Charges)", "Add or Deduct (Purchase Taxes and Charges)",
                 "Consider Tax or Charge for (Purchase Taxes and Charges)", "Batch No (Items)"])

    save_to_csv(purchase_invoices, 'purchase_invoices.csv',
                ["ID", "Credit To", "Date", "Due Date", "Series", "Supplier", "Item (Items)",
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
                 "Type (Purchase Taxes and Charges)", "Expense Head (Items)", "Deferred Expense Account (Items)"])

    save_to_csv(payment_entries, 'payment_entries.csv',
                ["ID", "Account Currency (From)", "Account Currency (To)", "Account Paid From", "Account Paid To",
                 "Company", "Paid Amount", "Paid Amount (Company Currency)", "Payment Type", "Posting Date",
                 "Received Amount", "Received Amount (Company Currency)", "Series", "Source Exchange Rate",
                 "Target Exchange Rate", "ID (Payment References)", "Type (Payment References)",
                 "Name (Payment References)", "ID (Advance Taxes and Charges)",
                 "Account Head (Advance Taxes and Charges)", "Add Or Deduct (Advance Taxes and Charges)",
                 "Description (Advance Taxes and Charges)", "Party Type", "Party", "Cheque/Reference Date",
                 "Cheque/Reference No", "Type (Advance Taxes and Charges)"])

    print("Datengenerierung abgeschlossen. Ausgabedateien wurden im Verzeichnis 'Generated_CSV' gespeichert.")


if __name__ == "__main__":
    main()
