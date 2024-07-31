import csv
import random

"""
OBSOLET
"""
def load_sales_persons(filename):
    sales_persons = []
    with open(filename, 'r', newline='', encoding='utf-8') as input_file:
        reader = csv.DictReader(input_file)
        for row in reader:
            sales_persons.append(row['Sales Person Name'])
    return sales_persons


def generate_territories(sales_persons):
    territories = [
        {
            "Territory Name": "Germany",
            "Is Group": 0,
            "Parent Territory": "All Territories",
            "Territory Manager": random.choice(sales_persons)
        },
        {
            "Territory Name": "Austria",
            "Is Group": 0,
            "Parent Territory": "All Territories",
            "Territory Manager": random.choice(sales_persons)
        },
        {
            "Territory Name": "Switzerland",
            "Is Group": 0,
            "Parent Territory": "All Territories",
            "Territory Manager": random.choice(sales_persons)
        }
    ]
    return territories


def save_to_csv(territories, filename):
    fieldnames = [
        "Territory Name", "Is Group", "old_parent", "Parent Territory",
        "Territory Manager", "ID (Targets)", "Fiscal Year (Targets)",
        "Item Group (Targets)", "Target  Amount (Targets)",
        "Target Distribution (Targets)", "Target Qty (Targets)"
    ]

    with open(filename, 'w', newline='', encoding='utf-8') as output_file:
        writer = csv.DictWriter(output_file, fieldnames=fieldnames)
        writer.writeheader()
        for territory in territories:
            writer.writerow(territory)


def main():
    sales_persons = load_sales_persons('../new csv/sales_persons.csv')
    territories = generate_territories(sales_persons)
    save_to_csv(territories, '../new csv/territories.csv')
    print(f"Generated {len(territories)} territories and saved to territories.csv")


if __name__ == "__main__":
    main()