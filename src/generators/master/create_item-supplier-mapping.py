from pathlib import Path
from typing import List, Dict
import csv
import random
from src.config.settings import MASTER_DATA_DIR, OUTPUT_DIR


def load_csv_data(filename: str, directory: Path) -> List[Dict]:
    """Load data from CSV file."""
    try:
        filepath = directory / filename
        with open(filepath, 'r', encoding='utf-8') as f:
            return list(csv.DictReader(f))
    except Exception as e:
        print(f"Error loading CSV file {filename}: {str(e)}")
        raise


def generate_item_supplier_mapping(items: List[Dict], suppliers: List[Dict]) -> Dict[str, str]:
    """Generate mapping between items and suppliers."""
    mapping = {}
    for item in items:
        # Assign random supplier for each item
        supplier = random.choice(suppliers)
        mapping[item['Item Code']] = supplier['ID']
    return mapping


def save_mapping_to_csv(mapping: Dict[str, str], filepath: Path):
    """Save item-supplier mapping to CSV file."""
    try:
        # Ensure the output directory exists
        filepath.parent.mkdir(parents=True, exist_ok=True)

        with open(filepath, 'w', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            writer.writerow(['Item Code', 'Supplier ID'])
            for item_code, supplier_id in mapping.items():
                writer.writerow([item_code, supplier_id])

        print(f"Item-supplier mapping saved to {filepath}")
    except Exception as e:
        print(f"Error saving mapping to CSV: {str(e)}")
        raise


def main():
    try:
        # Load items and suppliers from correct directories
        items = load_csv_data('items.csv', MASTER_DATA_DIR / 'base')
        suppliers = load_csv_data('suppliers.csv', MASTER_DATA_DIR / 'partners')

        print(f"Loaded {len(items)} items and {len(suppliers)} suppliers")

        # Generate mapping
        mapping = generate_item_supplier_mapping(items, suppliers)

        # Save to mapping directory
        output_path = MASTER_DATA_DIR / 'mappings' / 'item_supplier_mapping.csv'
        save_mapping_to_csv(mapping, output_path)

        print("Item-supplier mapping generation completed successfully")

    except Exception as e:
        print(f"Error during mapping generation: {str(e)}")
        raise


if __name__ == "__main__":
    main()