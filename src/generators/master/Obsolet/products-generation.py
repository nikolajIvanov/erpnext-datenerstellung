import csv
import random
from datetime import datetime, timedelta


def generate_product_code(prefix, number):
    return f"{prefix}-{number:04d}"


def generate_components():
    components = [
        ("Frame", "Bicycle Frame Type {}"),
        ("Fork", "Bicycle Fork Type {}"),
        ("Front Wheel", "Front Wheel Type {}"),
        ("Rear Wheel", "Rear Wheel Type {}"),
        ("Front Tire", "Front Tire Type {}"),
        ("Rear Tire", "Rear Tire Type {}"),
        ("Front Tube", "Front Tube Type {}"),
        ("Rear Tube", "Rear Tube Type {}"),
        ("Handlebar", "Handlebar Type {}"),
        ("Stem", "Stem Type {}"),
        ("Headset", "Headset Type {}"),
        ("Crankset", "Crankset Type {}"),
        ("Pedals", "Pedals Type {}"),
        ("Chain", "Chain Type {}"),
        ("Gear Set", "Gear Set Type {}"),
        ("Cassette", "Cassette Type {}"),
        ("Front Brake", "Front Brake Type {}"),
        ("Rear Brake", "Rear Brake Type {}"),
        ("Saddle", "Saddle Type {}"),
        ("Seatpost", "Seatpost Type {}"),
        ("Gear Cable Set", "Gear Cable Set Type {}"),
        ("Brake Cable Set", "Brake Cable Set Type {}"),
        ("Small Parts Kit", "Small Parts Kit Type {}"),
        ("Accessory Kit", "Accessory Kit Type {}"),
        ("E-Bike Motor", "E-Bike Motor Type {}"),
        ("E-Bike Battery", "E-Bike Battery Type {}"),
        ("E-Bike Controller", "E-Bike Controller Type {}"),
        ("E-Bike Display", "E-Bike Display Type {}"),
        ("E-Bike Wiring", "E-Bike Wiring Kit Type {}"),
        ("E-Bike Sensors", "E-Bike Sensors Kit Type {}")
    ]

    generated_components = []
    for i, (component_type, name_template) in enumerate(components, start=1):
        component = {
            "Item Code": generate_product_code("COMP", i),
            "Item Name": name_template.format(i),
            "Item Group": "Bicycle Components",
            "Default Unit of Measure": "Nos",
            "Allow Alternative Item": 1,
            "Is Stock Item": 1,
            "Include Item In Manufacturing": 1,
            "Opening Stock": random.randint(50, 200),
            "Valuation Rate": round(random.uniform(10, 500), 2),
            "Standard Rate": round(random.uniform(20, 1000), 2),
            "Description": f"High-quality {name_template.format(i).lower()} for bicycles and e-bikes",
            "Brand": random.choice(["VeloTech", "CyclePro", "GearMaster", "ElectroBike"]),
            "Warranty Period (in days)": random.choice([90, 180, 365, 730]),
            "Weight Per Unit": round(random.uniform(0.1, 5), 2),
            "Weight UOM": "Kg"
        }
        generated_components.append(component)
    return generated_components


def generate_bikes(num_bikes, is_ebike=False):
    bikes = []
    prefix = "EBIKE" if is_ebike else "BIKE"
    item_group = "E-Bikes" if is_ebike else "Bicycles"

    for i in range(num_bikes):
        bike = {
            "Item Code": generate_product_code(prefix, i + 1),
            "Item Name": f"{'E-Bike' if is_ebike else 'Bicycle'} Model {i + 1}",
            "Item Group": item_group,
            "Default Unit of Measure": "Nos",
            "Allow Alternative Item": 0,
            "Is Stock Item": 1,
            "Include Item In Manufacturing": 1,
            "Opening Stock": random.randint(10, 50),
            "Valuation Rate": round(random.uniform(300, 1500), 2),
            "Standard Rate": round(random.uniform(600, 3000), 2),
            "Description": f"High-performance {'e-bike' if is_ebike else 'bicycle'} suitable for various terrains",
            "Brand": "Velo",
            "Warranty Period (in days)": 730,
            "Weight Per Unit": round(random.uniform(10, 25), 2),
            "Weight UOM": "Kg"
        }
        if is_ebike:
            bike["Valuation Rate"] += 500
            bike["Standard Rate"] += 1000
        bikes.append(bike)
    return bikes


def generate_repair_services():
    services = [
        "Tire Change",
        "Brake Maintenance",
        "Gear Adjustment",
        "Chain Replacement",
        "Wheel Truing",
        "Complete Inspection",
        "E-Bike Diagnosis",
        "Battery Service",
        "Suspension Fork Service",
        "Frame Painting"
    ]
    return [{
        "Item Code": generate_product_code("SERV", i + 1),
        "Item Name": service,
        "Item Group": "Repair Services",
        "Default Unit of Measure": "Hrs",
        "Allow Alternative Item": 0,
        "Is Stock Item": 0,
        "Include Item In Manufacturing": 0,
        "Valuation Rate": 0,
        "Standard Rate": round(random.uniform(30, 150), 2),
        "Description": f"Professional bicycle repair service: {service.lower()}",
    } for i, service in enumerate(services)]


def save_to_csv(items, filename):
    fieldnames = [
        "Item Code", "Item Name", "Item Group", "Default Unit of Measure",
        "Allow Alternative Item", "Is Stock Item", "Include Item In Manufacturing",
        "Opening Stock", "Valuation Rate", "Standard Rate", "Description",
        "Brand", "Warranty Period (in days)", "Weight Per Unit", "Weight UOM"
    ]

    with open(filename, 'w', newline='', encoding='utf-8') as output_file:
        writer = csv.DictWriter(output_file, fieldnames=fieldnames)
        writer.writeheader()
        for item in items:
            writer.writerow({k: item.get(k, '') for k in fieldnames})


def main():
    components = generate_components()
    normal_bikes = generate_bikes(10)
    e_bikes = generate_bikes(5, is_ebike=True)
    repair_services = generate_repair_services()

    all_items = components + normal_bikes + e_bikes + repair_services

    save_to_csv(all_items, '../generated/products.csv')
    print(f"Generated {len(all_items)} items and saved to products.csv")


if __name__ == "__main__":
    main()
