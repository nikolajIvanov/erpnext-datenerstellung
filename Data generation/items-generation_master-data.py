import random
import csv


def generate_product_code(prefix, number):
    return f"{prefix}-{number:04d}"


def generate_bikes(num_bikes, is_ebike=False):
    bikes = []
    prefix = "EBIKE" if is_ebike else "BIKE"
    item_group = "E-Bikes" if is_ebike else "Fahrräder"

    for i in range(num_bikes):
        bike = {
            "Item Code": generate_product_code(prefix, i + 1),
            "Item Name": f"{'E-Bike' if is_ebike else 'Fahrrad'} Modell {i + 1}",
            "Item Group": item_group,
            "Default Unit of Measure": "Nos",
            "Is Stock Item": 1,
            "Valuation Rate": round(random.uniform(300, 800), 2),
            "Standard Selling Rate": round(random.uniform(600, 1500), 2),
            "Description": f"{'E-Bike' if is_ebike else 'Fahrrad'} Modell {i + 1} Beschreibung"
        }
        if is_ebike:
            bike["Standard Selling Rate"] += 500  # E-Bikes sind teurer
        bikes.append(bike)
    return bikes


def generate_components(num_components):
    components = []
    component_types = ["Rahmen", "Gabel", "Lenker", "Sattel", "Reifen", "Schaltung", "Bremsen", "Pedale", "Kette",
                       "Laufrad"]

    for i in range(num_components):
        component_type = random.choice(component_types)
        component = {
            "Item Code": generate_product_code("COMP", i + 1),
            "Item Name": f"{component_type} Typ {i + 1}",
            "Item Group": "Fahrradkomponenten",
            "Default Unit of Measure": "Nos",
            "Is Stock Item": 1,
            "Valuation Rate": round(random.uniform(10, 200), 2),
            "Standard Selling Rate": round(random.uniform(20, 400), 2),
            "Description": f"{component_type} Typ {i + 1} Beschreibung"
        }
        components.append(component)
    return components


def save_to_csv(items, filename):
    fieldnames = [
        "Item Code", "Item Name", "Item Group", "Default Unit of Measure",
        "Is Stock Item", "Valuation Rate", "Standard Selling Rate", "Description"
    ]

    with open(filename, 'w', newline='', encoding='utf-8') as output_file:
        writer = csv.DictWriter(output_file, fieldnames=fieldnames)
        writer.writeheader()
        for item in items:
            writer.writerow({k: item.get(k, '') for k in fieldnames})


def main():
    normal_bikes = generate_bikes(5)
    e_bikes = generate_bikes(5, is_ebike=True)
    components = generate_components(30)

    all_items = normal_bikes + e_bikes + components

    save_to_csv(all_items, '../new csv/products.csv')
    print(f"Generated {len(all_items)} products and saved to products.csv")


if __name__ == "__main__":
    main()