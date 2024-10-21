import random
import csv
from faker import Faker

# Initialisierung des Faker-Generators für deutschsprachige Daten
fake = Faker('de_DE')


def generate_product_code(prefix, number):
    return f"{prefix}-{number:04d}"


def generate_serial_no(prefix):
    return f"{prefix}-{fake.unique.random_number(digits=8)}"


def generate_batch_no(prefix):
    return f"{prefix}-{fake.date_this_year().strftime('%Y%m%d')}-{fake.random_number(digits=4)}"


def get_expense_account(item_group):
    if item_group in ["Fahrräder", "E-Bikes"]:
        return "5000 - Aufwendungen f. Roh-, Hilfs- und Betriebsstoffe und f. bezogene Waren - B"
    elif item_group == "Fahrradkomponenten":
        return "5000 - Aufwendungen f. Roh-, Hilfs- und Betriebsstoffe und f. bezogene Waren - B"
    else:
        return "5000 - Aufwendungen f. Roh-, Hilfs- und Betriebsstoffe und f. bezogene Waren - B"

def generate_bike_description(bike_type, is_ebike):
    bike_descriptions = {
        "City": "Perfekt für den urbanen Alltag. Komfortabel und wendig für Fahrten in der Stadt.",
        "Trekking": "Vielseitig einsetzbar für lange Touren und Alltagsfahrten. Robust und bequem.",
        "Mountain": "Geeignet für anspruchsvolles Gelände. Stabil und mit hervorragender Federung.",
        "Race": "Aerodynamisch und leicht für maximale Geschwindigkeit auf der Straße."
    }
    base_desc = bike_descriptions[bike_type]
    if is_ebike:
        return f"E-Bike: {base_desc} Mit leistungsstarkem Elektromotor für mühelose Fahrten."
    return base_desc

def generate_component_description(component_type, variant):
    descriptions = {
        "Rahmen": {
            "Aluminium": "Leichter und steifer Aluminiumrahmen für optimale Kraftübertragung.",
            "Carbon": "Hochmoderner Carbonrahmen für maximale Leichtigkeit und Stabilität.",
            "Stahl": "Klassischer Stahlrahmen für hohen Komfort und Langlebigkeit."
        },
        "Gabel": {
            "Starr": "Robuste Starrgabel für direkte Kraftübertragung und geringes Gewicht.",
            "Federgabel": "Hochwertige Federgabel für optimalen Fahrkomfort und Kontrolle im Gelände."
        },
        "Lenker": {
            "Flatbar": "Gerader Lenker für aufrechte Sitzposition und gute Kontrolle.",
            "Riserbar": "Erhöhter Lenker für entspannte Haltung und gute Übersicht.",
            "Dropbar": "Rennlenker für aerodynamische Position und verschiedene Griffmöglichkeiten."
        },
        "Sattel": {
            "Komfort": "Breiter, gepolsterter Sattel für maximalen Sitzkomfort auf längeren Fahrten.",
            "Sport": "Ergonomischer Sportsattel für effizientes Pedalieren und Druckentlastung.",
            "Gel": "Gel-Sattel für stoßabsorbierende Eigenschaften und hohen Komfort."
        },
        "Schaltung": {
            "7-Gang": "Zuverlässige 7-Gang-Schaltung für den Alltagsgebrauch.",
            "9-Gang": "Vielseitige 9-Gang-Schaltung für verschiedene Geländeprofile.",
            "11-Gang": "Hochwertige 11-Gang-Schaltung für präzise Gangwechsel und große Bandbreite.",
            "1x12 MTB": "Moderne 1x12 MTB-Schaltung für einfache Bedienung und große Übersetzungsbandbreite.",
            "2x11 Rennrad": "Klassische 2x11 Rennradschaltung für optimale Abstufung und Effizienz."
        },
    }
    return descriptions.get(component_type, {}).get(variant, f"{component_type} {variant}: Hochwertige Komponente für optimale Leistung.")


def generate_bike_models(num_regular_bikes, num_ebikes):
    bikes = []
    serial_numbers = []
    for i in range(num_regular_bikes + num_ebikes):
        is_ebike = i < num_ebikes
        prefix = "EBIKE" if is_ebike else "BIKE"
        item_group = "E-Bikes" if is_ebike else "Fahrräder"
        bike_type = random.choice(["City", "Trekking", "Mountain", "Race"])
        item_code = generate_product_code(prefix, i + 1)

        model = {
            "Item Code": item_code,
            "Item Name": f"Velo {'E-' if is_ebike else ''}{bike_type} {fake.random_int(min=100, max=999)}",
            "Item Group": item_group,
            "Default Unit of Measure": "Nos",
            "Allow Alternative Item": 1,
            "Allow Negative Stock": 0,
            "Allow Purchase": 0,
            "Allow Sales": 1,
            "Description": generate_bike_description(bike_type, is_ebike),
            "Has Serial No": 1,
            "Serial Number Series": f"{prefix}-SERIES-",
            "Include Item In Manufacturing": 1,
            "Is Fixed Asset": 0,
            "Maintain Stock": 1,
            "Valuation Rate": round(random.uniform(300, 800), 2),
            "Standard Selling Rate": round(random.uniform(600, 2000), 2),
            "Warranty Period (in days)": random.randint(365, 730),
            "Weight Per Unit": round(random.uniform(10, 20), 2),
            "Weight UOM": "Kg",
            "Default Expense Account (Item Defaults)": get_expense_account(item_group)  # Neue Zeile
        }
        bikes.append(model)

        # Generate one Serial Number for each bike
        serial_numbers.append({
            "Company": "Velo GmbH",
            "Item Code": item_code,
            "Serial No": generate_serial_no(prefix)
        })

    return bikes, serial_numbers


def generate_detailed_components(num_components):
    components = []
    batch_numbers = []
    common_components = {
        "Rahmen": ["Aluminium", "Carbon", "Stahl"],
        "Gabel": ["Starr", "Federgabel"],
        "Lenker": ["Flatbar", "Riserbar", "Dropbar"],
        "Sattel": ["Komfort", "Sport", "Gel"],
        "Reifen": ["Straße 28\"", "Gelände 26\"", "Allround 27.5\"", "Gravel 29\""],
        "Schaltung": ["7-Gang", "9-Gang", "11-Gang", "1x12 MTB", "2x11 Rennrad"],
        "Bremsen": ["Scheibenbremsen hydraulisch", "Scheibenbremsen mechanisch", "Felgenbremsen"],
        "Pedale": ["Plattform", "Klickpedale", "Kombipedale"],
        "Kette": ["8-fach", "9-fach", "11-fach", "12-fach"],
        "Laufräder": ["26 Zoll", "27,5 Zoll", "28 Zoll", "29 Zoll"],
        "Sattelstütze": ["Gefedert", "Starr", "Teleskop"],
        "Griffe": ["Ergonomisch", "Standard", "Leder", "Schaumstoff"],
        "Steuersatz": ["Integriert", "Semi-integriert", "Gewinde"],
        "Vorbau": ["Standardvorbau", "Verstellbarer Vorbau"],
        "Kurbel": ["1-fach", "2-fach", "3-fach"],
    }

    ebike_specific_components = {
        "Akku": ["36V 10Ah", "36V 15Ah", "48V 10Ah", "48V 15Ah", "Zusatzakku"],
        "Motor": ["Mittelmotor 250W", "Mittelmotor 500W", "Nabenmotor 250W", "Nabenmotor Vorderrad"],
        "Display": ["LCD", "LED", "Smartphone-Integration", "Minimaldisplay"],
        "Controller": ["Standard", "Leistungsstark", "Tuning-Kit"],
    }

    all_components = list(common_components.items()) + list(ebike_specific_components.items())

    for i in range(num_components):
        component_type, variants = random.choice(all_components)
        variant = random.choice(variants)
        item_code = generate_product_code("COMP", i + 1)

        component = {
            "Item Code": item_code,
            "Item Name": f"{component_type} {variant}",
            "Item Group": "Fahrradkomponenten",
            "Default Unit of Measure": "Nos",
            "Allow Alternative Item": 1,
            "Allow Negative Stock": 0,
            "Allow Purchase": 1,
            "Allow Sales": 1,
            "Description": generate_component_description(component_type, variant),
            "Has Batch No": 1,
            "Batch Number Series": f"BATCH-{component_type[:3].upper()}-",
            "Include Item In Manufacturing": 1,
            "Is Fixed Asset": 0,
            "Maintain Stock": 1,
            "Valuation Rate": round(random.uniform(10, 200), 2),
            "Standard Selling Rate": round(random.uniform(20, 400), 2),
            "Warranty Period (in days)": random.randint(90, 365),
            "Weight Per Unit": round(random.uniform(0.1, 5), 2),
            "Weight UOM": "Kg",
            "Default Expense Account (Item Defaults)": get_expense_account("Fahrradkomponenten")  # Neue Zeile
        }
        components.append(component)

        # Generate one Batch Number for each component
        batch_numbers.append({
            "Batch ID": generate_batch_no(f"BATCH-{component_type[:3].upper()}"),
            "Item": item_code
        })

    return components, batch_numbers


def save_to_csv(items, filename):
    fieldnames = [
        "Default Unit of Measure", "Item Code", "Item Group", "Allow Alternative Item",
        "Allow Negative Stock", "Allow Purchase", "Allow Sales", "Description",
        "Has Batch No", "Has Serial No", "Include Item In Manufacturing",
        "Is Fixed Asset", "Item Name", "Maintain Stock", "Standard Selling Rate",
        "Valuation Rate", "Warranty Period (in days)", "Weight Per Unit", "Weight UOM",
        "Serial Number Series", "Batch Number Series", "Default Expense Account (Item Defaults)"
    ]

    with open(filename, 'w', newline='', encoding='utf-8') as output_file:
        writer = csv.DictWriter(output_file, fieldnames=fieldnames)
        writer.writeheader()
        for item in items:
            writer.writerow({k: item.get(k, '') for k in fieldnames})


def save_serial_numbers_to_csv(serial_numbers, filename):
    fieldnames = ["Company", "Item Code", "Serial No"]
    with open(filename, 'w', newline='', encoding='utf-8') as output_file:
        writer = csv.DictWriter(output_file, fieldnames=fieldnames)
        writer.writeheader()
        for serial_number in serial_numbers:
            writer.writerow(serial_number)


def save_batch_numbers_to_csv(batch_numbers, filename):
    fieldnames = ["Batch ID", "Item"]
    with open(filename, 'w', newline='', encoding='utf-8') as output_file:
        writer = csv.DictWriter(output_file, fieldnames=fieldnames)
        writer.writeheader()
        for batch_number in batch_numbers:
            writer.writerow(batch_number)


def main():
    # Hier können Sie die gewünschten Werte direkt eintragen
    num_regular_bikes = 1  # Anzahl der normalen Fahrräder
    num_ebikes = 1  # Anzahl der E-Bikes
    components_per_bike = 25  # Durchschnittliche Anzahl der Komponenten pro Fahrrad

    total_bikes = num_regular_bikes + num_ebikes
    num_components = total_bikes * components_per_bike

    bikes, bike_serial_numbers = generate_bike_models(num_regular_bikes, num_ebikes)
    components, component_batch_numbers = generate_detailed_components(num_components)

    all_items = bikes + components

    save_to_csv(all_items, '../Generated_CSV/items.csv')
    save_serial_numbers_to_csv(bike_serial_numbers, '../Generated_CSV/serial_numbers.csv')
    save_batch_numbers_to_csv(component_batch_numbers, '../Generated_CSV/batch_numbers.csv')

    print(f"Generated {num_regular_bikes} regular bikes, {num_ebikes} e-bikes, and {len(components)} components.")
    print(f"Generated {len(bike_serial_numbers)} serial numbers and {len(component_batch_numbers)} batch numbers.")
    print("Data saved to items.csv, serial_numbers.csv, and batch_numbers.csv")


if __name__ == "__main__":
    main()