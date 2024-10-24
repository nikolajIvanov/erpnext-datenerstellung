import csv
import random
import os


class Config:
    BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    INPUT_DIR = os.path.join(BASE_DIR, 'master')
    OUTPUT_DIR = os.path.join(BASE_DIR, 'generated')
    MAPPING_FILE = 'item_supplier_mapping.csv'


def load_csv_data(filename):
    with open(os.path.join(Config.INPUT_DIR, filename), 'r', encoding='utf-8') as f:
        return list(csv.DictReader(f))


def generate_item_supplier_mapping(items, suppliers):
    mapping = {}
    for item in items:
        # Wähle einen zufälligen Lieferanten für jedes Item
        supplier = random.choice(suppliers)
        mapping[item['Item Code']] = supplier['ID']  # Verwende Supplier ID statt Name
    return mapping


def save_mapping_to_csv(mapping, filename):
    with open(os.path.join(Config.OUTPUT_DIR, filename), 'w', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        writer.writerow(['Item Code', 'Supplier ID'])  # Ändere die Spaltenüberschrift
        for item_code, supplier_id in mapping.items():
            writer.writerow([item_code, supplier_id])


def main():
    items = load_csv_data('items.csv')
    suppliers = load_csv_data('suppliers.csv')

    mapping = generate_item_supplier_mapping(items, suppliers)
    save_mapping_to_csv(mapping, Config.MAPPING_FILE)
    print(f"Item-Lieferanten-Zuordnung wurde in {Config.MAPPING_FILE} gespeichert.")


if __name__ == "__main__":
    main()
