import csv
from datetime import datetime, timedelta
import random
import os


class Config:
    BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    INPUT_DIR = os.path.join(BASE_DIR, 'master_data_csv')
    OUTPUT_DIR = os.path.join(BASE_DIR, 'Generated_CSV')
    START_DATE = datetime(2023, 1, 1)
    END_DATE = datetime(2023, 12, 31)
    PRODUCTION_WAREHOUSE = "Lager Stuttgart - B"
    FINISHED_GOODS_WAREHOUSE = "Lager Stuttgart - B"


def load_csv_data(filename):
    with open(os.path.join(Config.INPUT_DIR, filename), 'r', encoding='utf-8') as f:
        return list(csv.DictReader(f))


def generate_id(prefix, date):
    year = date.year
    number = random.randint(1, 99999)
    return f"{prefix}-{year}-{number:05d}"


def random_date(start_date, end_date):
    return start_date + timedelta(
        seconds=random.randint(0, int((end_date - start_date).total_seconds()))
    )


def load_bom_data():
    bom_data = {}
    for filename in ['bom_bike.csv', 'bom_ebike.csv']:
        with open(os.path.join(Config.INPUT_DIR, filename), 'r', encoding='utf-8') as f:
            reader = csv.reader(f)
            header = next(reader)
            bom_info = next(reader)
            bom_id = bom_info[0]
            items = [dict(zip(header, row)) for row in reader if row[10]]  # Only include rows with an Item Code
            bom_data[bom_id] = {
                'ID': bom_id,
                'Item': bom_info[4],
                'Item Name': bom_info[9],
                'Items': items
            }
    return bom_data


def load_batch_numbers():
    batch_data = load_csv_data('batch_numbers.csv')
    return {batch['Item']: batch['Batch ID'] for batch in batch_data}


def generate_work_orders(num_orders, bom_data):
    work_orders = []
    for _ in range(num_orders):
        wo_date = random_date(Config.START_DATE, Config.END_DATE)
        bom_id, bom = random.choice(list(bom_data.items()))
        work_order = {
            "ID": generate_id("MFG-WO", wo_date),
            "BOM No": bom_id,
            "Company": "Velo GmbH",
            "Item To Manufacture": bom['Item'],
            "Planned Start Date": wo_date.strftime("%Y-%m-%d %H:%M:%S"),
            "Qty To Manufacture": random.randint(1, 10),
            "Series": "MFG-WO-.YYYY.-",
            "Status": "Submitted",
            "Has Batch No": 0,
            "Has Serial No": 1,
            "Work-in-Progress Warehouse": Config.PRODUCTION_WAREHOUSE,
            "Source Warehouse": Config.PRODUCTION_WAREHOUSE,
            "Target Warehouse": Config.FINISHED_GOODS_WAREHOUSE
        }
        work_orders.append(work_order)
    return work_orders


def generate_stock_entries(work_orders, bom_data, batch_numbers):
    material_transfers = []
    manufactures = []
    for wo in work_orders:
        bom = bom_data[wo['BOM No']]

        entry_id = generate_id("MAT-STE", datetime.strptime(wo['Planned Start Date'], "%Y-%m-%d %H:%M:%S"))

        # Material Transfer for Manufacture
        transfer_entry = {
            "ID": entry_id,
            "Company": "Velo GmbH",
            "Series": "MAT-STE-.YYYY.-",
            "Stock Entry Type": "Material Transfer for Manufacture",
            "BOM No": wo['BOM No'],
            "From BOM": 1,
            "Work Order": wo['ID'],
            "Default Source Warehouse": Config.PRODUCTION_WAREHOUSE,
            "Default Target Warehouse": Config.FINISHED_GOODS_WAREHOUSE,
            "Add to Transit": 0,
            "Items": []
        }

        for item in bom['Items']:
            transfer_entry["Items"].append({
                "Conversion Factor (Items)": 1.0,
                "Item Code (Items)": item['Item Code (Items)'],
                "Qty (Items)": float(item['Qty (Items)']) * wo['Qty To Manufacture'],
                "Qty as per Stock UOM (Items)": float(item['Qty (Items)']) * wo['Qty To Manufacture'],
                "Stock UOM (Items)": item['UOM (Items)'],
                "UOM (Items)": item['UOM (Items)'],
                "Batch No (Items)": batch_numbers.get(item['Item Code (Items)'], "")
            })

        material_transfers.append(transfer_entry)

        # Manufacture
        manufacture_entry = transfer_entry.copy()
        manufacture_entry["Stock Entry Type"] = "Manufacture"
        manufacture_entry["Default Source Warehouse"] = Config.PRODUCTION_WAREHOUSE
        manufacture_entry["Default Target Warehouse"] = Config.FINISHED_GOODS_WAREHOUSE
        manufacture_entry["Items"].append({
            "Conversion Factor (Items)": 1.0,
            "Item Code (Items)": wo['Item To Manufacture'],
            "Qty (Items)": wo['Qty To Manufacture'],
            "Qty as per Stock UOM (Items)": wo['Qty To Manufacture'],
            "Stock UOM (Items)": "Nos",
            "UOM (Items)": "Nos",
            "Batch No (Items)": ""
        })

        manufactures.append(manufacture_entry)

    return material_transfers, manufactures


def save_to_csv(data, filename, fieldnames):
    with open(os.path.join(Config.OUTPUT_DIR, filename), 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames, extrasaction='ignore')
        writer.writeheader()
        for entry in data:
            if 'Items' in entry:
                for item in entry['Items']:
                    row = {**entry, **item}
                    writer.writerow(row)
            else:
                writer.writerow(entry)


def main(num_work_orders):
    bom_data = load_bom_data()
    print(f"Loaded {len(bom_data)} BOMs")

    batch_numbers = load_batch_numbers()
    print(f"Loaded {len(batch_numbers)} batch numbers")

    work_orders = generate_work_orders(num_work_orders, bom_data)
    print(f"Generated {len(work_orders)} work orders")

    material_transfers, manufactures = generate_stock_entries(work_orders, bom_data, batch_numbers)
    print(f"Generated {len(material_transfers)} material transfers and {len(manufactures)} manufactures")

    # Save generated data to CSV files
    save_to_csv(work_orders, 'work_orders.csv',
                ["ID", "BOM No", "Company", "Item To Manufacture", "Planned Start Date",
                 "Qty To Manufacture", "Series", "Status", "Has Batch No", "Has Serial No",
                 "Work-in-Progress Warehouse", "Source Warehouse", "Target Warehouse"])

    save_to_csv(material_transfers, 'stock_entries_material_transfer.csv',
                ["ID", "Company", "Series", "Stock Entry Type", "BOM No", "From BOM", "Work Order",
                 "Default Source Warehouse", "Default Target Warehouse", "Add to Transit",
                 "Conversion Factor (Items)", "Item Code (Items)", "Qty (Items)",
                 "Qty as per Stock UOM (Items)", "Stock UOM (Items)", "UOM (Items)", "Batch No (Items)"])

    save_to_csv(manufactures, 'stock_entries_manufacture.csv',
                ["ID", "Company", "Series", "Stock Entry Type", "BOM No", "From BOM", "Work Order",
                 "Default Source Warehouse", "Default Target Warehouse", "Add to Transit",
                 "Conversion Factor (Items)", "Item Code (Items)", "Qty (Items)",
                 "Qty as per Stock UOM (Items)", "Stock UOM (Items)", "UOM (Items)", "Batch No (Items)"])

    print("Data generation completed. Output files have been saved in the 'Generated_CSV' directory.")


if __name__ == "__main__":
    main(num_work_orders=10)
