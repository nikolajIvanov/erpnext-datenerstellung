import csv
import random
import os


class Config:
    BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    INPUT_DIR = os.path.join(BASE_DIR, 'Master-Data_Processed_CSV')
    OUTPUT_DIR = os.path.join(BASE_DIR, 'Generated_CSV')
    DEFAULT_WAREHOUSE = "Lager Stuttgart - B"


def load_items(filename):
    items = []
    with open(os.path.join(Config.INPUT_DIR, filename), 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            items.append(row)
    return items


def get_component(components, component_type):
    matching_components = [c for c in components if component_type.lower() in c['Item Name'].lower()]
    return random.choice(matching_components) if matching_components else None


def generate_bom(bikes, components):
    common_components = [
        "Rahmen", "Gabel", "Lenker", "Sattel", "Reifen", "Schaltung", "Bremsen", "Pedale",
        "Kette", "Laufräder", "Sattelstütze", "Griffe", "Steuersatz", "Vorbau", "Kurbel"
    ]
    ebike_components = ["Akku", "Motor", "Display", "Controller"]

    boms = []
    for bike in bikes:
        bom = {
            "ID": f"BOM-{bike['Item Code']}-001",
            "Company": "Velo GmbH",
            "Conversion Rate": 1.0,
            "Currency": "EUR",
            "Item": bike['Item Code'],
            "Quantity": 1.0,
            "Default Source Warehouse": Config.DEFAULT_WAREHOUSE,
            "Default Target Warehouse": Config.DEFAULT_WAREHOUSE,
            "Item Description": bike['Description'],
            "Item Name": bike['Item Name'],
            "Items": []
        }

        # Add common components
        for component_type in common_components:
            component = get_component(components, component_type)
            if component:
                bom_item = {
                    "Item Code (Items)": component['Item Code'],
                    "Qty (Items)": 1.0,
                    "Rate (Items)": float(component['Valuation Rate']),
                    "UOM (Items)": component['Default Unit of Measure']
                }
                bom["Items"].append(bom_item)

        # Add E-Bike specific components if it's an E-Bike
        if bike['Item Group'] == 'E-Bikes':
            for component_type in ebike_components:
                component = get_component(components, component_type)
                if component:
                    bom_item = {
                        "Item Code (Items)": component['Item Code'],
                        "Qty (Items)": 1.0,
                        "Rate (Items)": float(component['Valuation Rate']),
                        "UOM (Items)": component['Default Unit of Measure']
                    }
                    bom["Items"].append(bom_item)

        boms.append(bom)
    return boms


def save_bom_to_csv(boms, filename):
    fieldnames = [
        "ID", "Company", "Conversion Rate", "Currency", "Item", "Quantity",
        "Default Source Warehouse", "Default Target Warehouse", "Item Description", "Item Name",
        "Item Code (Items)", "Qty (Items)", "Rate (Items)", "UOM (Items)"
    ]

    with open(os.path.join(Config.OUTPUT_DIR, filename), 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames, delimiter=';')
        writer.writeheader()
        for bom in boms:
            main_row = {field: bom[field] for field in fieldnames[:10]}
            writer.writerow(main_row)
            for item in bom["Items"]:
                item_row = {**{field: "" for field in fieldnames[:10]}, **item}
                writer.writerow(item_row)


def main():
    # Load items
    items = load_items('items.csv')

    # Separate bikes and components
    bikes = [item for item in items if item['Item Group'] in ['Fahrräder', 'E-Bikes']]
    components = [item for item in items if item['Item Group'] == 'Fahrradkomponenten']

    # Generate BOMs
    boms = generate_bom(bikes, components)

    # Save BOMs to CSV
    save_bom_to_csv(boms, 'bom.csv')

    print(f"Generated {len(boms)} BOMs and saved to bom.csv")


if __name__ == "__main__":
    main()