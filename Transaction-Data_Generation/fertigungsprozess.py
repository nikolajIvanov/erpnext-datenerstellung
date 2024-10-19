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
    PRODUCTION_WAREHOUSE = "Production Warehouse - V"
    FINISHED_GOODS_WAREHOUSE = "Finished Goods Warehouse - V"


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


def generate_production_plans(items, num_plans):
    production_plans = []
    for _ in range(num_plans):
        plan_date = random_date(Config.START_DATE, Config.END_DATE)
        item = random.choice(items)
        quantity = random.randint(10, 100)

        plan = {
            "ID": generate_id("MFG-PP", plan_date),
            "Item": item['Item Code'],
            "Item Name": item['Item Name'],
            "BOM No": f"BOM-{item['Item Code']}",  # Assuming BOM number follows this format
            "Planned Qty": quantity,
            "Warehouse": Config.FINISHED_GOODS_WAREHOUSE,
            "Planned Start Date": plan_date.strftime("%Y-%m-%d"),
            "Status": "Submitted"
        }
        production_plans.append(plan)
    return production_plans


def generate_work_orders(production_plans):
    work_orders = []
    for plan in production_plans:
        wo_date = datetime.strptime(plan['Planned Start Date'], "%Y-%m-%d") + timedelta(days=random.randint(1, 5))
        work_order = {
            "ID": generate_id("WO", wo_date),
            "Production Item": plan['Item'],
            "Item Name": plan['Item Name'],
            "BOM No": plan['BOM No'],
            "Qty To Manufacture": plan['Planned Qty'],
            "Planned Start Date": plan['Planned Start Date'],
            "Actual Start Date": wo_date.strftime("%Y-%m-%d"),
            "Planned End Date": (wo_date + timedelta(days=random.randint(1, 7))).strftime("%Y-%m-%d"),
            "Status": "In Process",
            "Production Plan": plan['ID'],
            "Source Warehouse": Config.PRODUCTION_WAREHOUSE,
            "Target Warehouse": Config.FINISHED_GOODS_WAREHOUSE
        }
        work_orders.append(work_order)
    return work_orders


def generate_stock_entries(work_orders, items):
    stock_entries = []
    for wo in work_orders:
        # Generate Material Transfer for Manufacture
        transfer_date = datetime.strptime(wo['Actual Start Date'], "%Y-%m-%d")
        transfer_entry = {
            "ID": generate_id("STE", transfer_date),
            "Stock Entry Type": "Material Transfer for Manufacture",
            "Posting Date": transfer_date.strftime("%Y-%m-%d"),
            "From Warehouse": Config.PRODUCTION_WAREHOUSE,
            "To Warehouse": wo['Source Warehouse'],
            "Work Order": wo['ID'],
            "Items": []  # This would be filled with required components based on BOM
        }
        stock_entries.append(transfer_entry)

        # Generate Manufacture entry
        manufacture_date = datetime.strptime(wo['Planned End Date'], "%Y-%m-%d")
        manufacture_entry = {
            "ID": generate_id("STE", manufacture_date),
            "Stock Entry Type": "Manufacture",
            "Posting Date": manufacture_date.strftime("%Y-%m-%d"),
            "From Warehouse": wo['Source Warehouse'],
            "To Warehouse": wo['Target Warehouse'],
            "Work Order": wo['ID'],
            "Items": [{
                "Item Code": wo['Production Item'],
                "Qty": wo['Qty To Manufacture'],
                "Transfer Qty": wo['Qty To Manufacture'],
                "UOM": next(
                    item['Default Unit of Measure'] for item in items if item['Item Code'] == wo['Production Item'])
            }]
        }
        stock_entries.append(manufacture_entry)

    return stock_entries


def save_to_csv(data, filename, fieldnames):
    with open(os.path.join(Config.OUTPUT_DIR, filename), 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames, extrasaction='ignore')
        writer.writeheader()
        writer.writerows(data)


def main(num_production_plans):
    items = load_csv_data('items.csv')
    print(f"Loaded {len(items)} items")

    production_plans = generate_production_plans(items, num_production_plans)
    print(f"Generated {len(production_plans)} production plans")

    work_orders = generate_work_orders(production_plans)
    print(f"Generated {len(work_orders)} work orders")

    stock_entries = generate_stock_entries(work_orders, items)
    print(f"Generated {len(stock_entries)} stock entries")

    # Save generated data to CSV files
    save_to_csv(production_plans, 'production_plans.csv',
                ["ID", "Item", "Item Name", "BOM No", "Planned Qty", "Warehouse", "Planned Start Date", "Status"])

    save_to_csv(work_orders, 'work_orders.csv',
                ["ID", "Production Item", "Item Name", "BOM No", "Qty To Manufacture", "Planned Start Date",
                 "Actual Start Date", "Planned End Date", "Status", "Production Plan", "Source Warehouse",
                 "Target Warehouse"])

    save_to_csv(stock_entries, 'stock_entries.csv',
                ["ID", "Stock Entry Type", "Posting Date", "From Warehouse", "To Warehouse", "Work Order"])

    print("Data generation completed. Output files have been saved in the 'Generated_CSV' directory.")


if __name__ == "__main__":
    main(num_production_plans=50)  # You can adjust the number of production plans as needed