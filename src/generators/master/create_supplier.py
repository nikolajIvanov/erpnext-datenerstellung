import csv
import random
from faker import Faker
import re

# Initialisierung des Faker-Generators für deutschsprachige Daten
fake = Faker('de_DE')

def remove_umlauts(text):
    """Replace umlauts and ß with their non-umlaut equivalents."""
    umlaut_map = {
        'ä': 'ae', 'ö': 'oe', 'ü': 'ue', 'ß': 'ss',
        'Ä': 'Ae', 'Ö': 'Oe', 'Ü': 'Ue'
    }
    for umlaut, replacement in umlaut_map.items():
        text = text.replace(umlaut, replacement)
    return text

def generate_supplier_code():
    return f"SUP-{random.randint(1000, 9999)}"

def generate_suppliers(num_suppliers):
    suppliers = []
    supplier_types = ["Company", "Individual", "Proprietorship", "Partnership"]

    for _ in range(num_suppliers):
        company_name = remove_umlauts(fake.company())

        supplier = {
            "ID": generate_supplier_code(),
            "Supplier Name": company_name,
            "Supplier Type": random.choice(supplier_types)
        }
        suppliers.append(supplier)
    return suppliers

def save_to_csv(suppliers, filename):
    fieldnames = ["ID", "Supplier Name", "Supplier Type"]

    with open(filename, 'w', newline='', encoding='utf-8') as output_file:
        writer = csv.DictWriter(output_file, fieldnames=fieldnames)
        writer.writeheader()
        for supplier in suppliers:
            writer.writerow(supplier)

def main():
    num_suppliers = 50  # Anzahl der zu generierenden Lieferanten
    suppliers = generate_suppliers(num_suppliers)
    save_to_csv(suppliers, '../data/generated/suppliers.csv')
    print(f"Generated {len(suppliers)} suppliers and saved to suppliers.csv")

if __name__ == "__main__":
    main()