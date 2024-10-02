import random
import csv
from faker import Faker

# Initialisierung des Faker-Generators für deutschsprachige Daten
fake = Faker('de_DE')


def generate_product_code(prefix, number):
    return f"{prefix}-{number:04d}"


def generate_bike_models(is_ebike=False):
    prefix = "EBIKE" if is_ebike else "BIKE"
    item_group = "E-Bikes" if is_ebike else "Fahrräder"
    bike_type = fake.random_element(elements=("City", "Trekking", "Mountain", "Race"))

    model = {
        "Item Code": generate_product_code(prefix, fake.random_int(min=1, max=999)),
        "Item Name": f"Velo {'E-' if is_ebike else ''}{bike_type} {fake.random_int(min=100, max=999)}",
        "Item Group": item_group,
        "Default Unit of Measure": "Nos",
        "Allow Alternative Item": 1,
        "Allow Negative Stock": 0,
        "Allow Purchase": 0,
        "Allow Sales": 1,
        "Description": fake.paragraph(nb_sentences=3, variable_nb_sentences=True),
        "Has Serial No": 1,
        "Include Item In Manufacturing": 1,
        "Is Fixed Asset": 0,
        "Maintain Stock": 1,
        "Valuation Rate": round(fake.pyfloat(min_value=300, max_value=800, right_digits=2), 2),
        "Standard Selling Rate": round(fake.pyfloat(min_value=600, max_value=2000, right_digits=2), 2),
        "Warranty Period (in days)": fake.random_int(min=365, max=730),
        "Weight Per Unit": round(fake.pyfloat(min_value=10, max_value=20, right_digits=2), 2),
        "Weight UOM": "Kg"
    }
    return model


def generate_detailed_components():
    components = []
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
        "Innenlager": ["BSA", "Pressfit", "Hollowtech"],
        "Felgen": ["Aluminium", "Carbon"],
        "Speichen": ["Standard", "Aero", "Straightpull"],
        "Naben": ["Standard", "Dynamo"],
        "Beleuchtung": ["LED-Set", "Dynamo-Set", "Akku-Set"],
        "Schutzbleche": ["Kunststoff", "Metall", "Carbon"],
        "Gepäckträger": ["Standard", "Lowrider", "Systemgepäckträger"],
        "Ständer": ["Seitenständer", "Hinterbauständer", "Zweibeinständer"],
        "Klingel": ["Standard", "Elektrisch"],
        "Reflektoren": ["Set", "Einzeln", "Integriert"],
        "Sattelklemme": ["Schnellspanner", "Schraubklemme"],
        "Flaschenhalter": ["Kunststoff", "Aluminium", "Carbon"],
        "Fahrradcomputer": ["Kabelgebunden", "Kabellos", "GPS"],
        "Kettenführung": ["1-fach", "2-fach", "ISCG05"],
        "Tretlager": ["BSA", "Pressfit", "BB30"],
    }

    ebike_specific_components = {
        "Akku": ["36V 10Ah", "36V 15Ah", "48V 10Ah", "48V 15Ah", "Zusatzakku"],
        "Motor": ["Mittelmotor 250W", "Mittelmotor 500W", "Nabenmotor 250W", "Nabenmotor Vorderrad"],
        "Display": ["LCD", "LED", "Smartphone-Integration", "Minimaldisplay"],
        "Ladegerät": ["2A", "4A", "Schnellladegerät", "Reiseladegerät"],
        "Controller": ["Standard", "Leistungsstark", "Tuning-Kit"],
        "Sensor": ["Tretkraftsensor", "Rotationssensor", "Kombisensor"],
    }

    additional_spare_parts = {
        "Schlauch": ["26\"", "27.5\"", "28\"", "29\""],
        "Bremsbeläge": ["Scheibenbremse organisch", "Scheibenbremse gesintert", "Felgenbremse"],
        "Brems-/Schaltzüge": ["Innenzug Bremse", "Innenzug Schaltung", "Außenhülle"],
        "Kettenöl": ["Trocken", "Nass", "Keramik"],
        "Reifenflickzeug": ["Set", "Flicken", "Reifenheber"],
        "Fahrradtasche": ["Lenkertasche", "Satteltasche", "Rahmentasche"],
        "Kettennieter": ["Standard", "Profi"],
        "Multitool": ["11-teilig", "16-teilig", "21-teilig"],
        "Pumpe": ["Standpumpe", "Minipumpe", "CO2-Pumpe"],
        "Luftdruckprüfer": ["Digital", "Analog"],
    }

    component_id = 1
    for component_dict in [common_components, ebike_specific_components, additional_spare_parts]:
        for component_type, variants in component_dict.items():
            for variant in variants:
                component = {
                    "Item Code": generate_product_code("COMP", component_id),
                    "Item Name": f"{component_type} {variant}",
                    "Item Group": "Fahrradkomponenten",
                    "Default Unit of Measure": "Nos",
                    "Allow Alternative Item": 1,
                    "Allow Negative Stock": 0,
                    "Allow Purchase": 1,
                    "Allow Sales": 1,
                    "Description": fake.paragraph(nb_sentences=2, variable_nb_sentences=True),
                    "Has Batch No": 1,
                    "Include Item In Manufacturing": 1,
                    "Is Fixed Asset": 0,
                    "Maintain Stock": 1,
                    "Valuation Rate": round(fake.pyfloat(min_value=10, max_value=200, right_digits=2), 2),
                    "Standard Selling Rate": round(fake.pyfloat(min_value=20, max_value=400, right_digits=2), 2),
                    "Warranty Period (in days)": fake.random_int(min=90, max=365),
                    "Weight Per Unit": round(fake.pyfloat(min_value=0.1, max_value=5, right_digits=2), 2),
                    "Weight UOM": "Kg"
                }
                components.append(component)
                component_id += 1

    return components


def save_to_csv(items, filename):
    fieldnames = [
        "Default Unit of Measure", "Item Code", "Item Group", "Allow Alternative Item",
        "Allow Negative Stock", "Allow Purchase", "Allow Sales", "Description",
        "Has Batch No", "Has Serial No", "Include Item In Manufacturing",
        "Is Fixed Asset", "Item Name", "Maintain Stock", "Standard Selling Rate",
        "Valuation Rate", "Warranty Period (in days)", "Weight Per Unit", "Weight UOM"
    ]

    with open(filename, 'w', newline='', encoding='utf-8') as output_file:
        writer = csv.DictWriter(output_file, fieldnames=fieldnames)
        writer.writeheader()
        for item in items:
            writer.writerow({k: item.get(k, '') for k in fieldnames})


def main():
    normal_bike = generate_bike_models()
    e_bike = generate_bike_models(is_ebike=True)
    components = generate_detailed_components()

    all_items = [normal_bike, e_bike] + components

    save_to_csv(all_items, '../Generated_CSV/products.csv')
    print(f"Generated {len(all_items)} items (2 bikes and {len(components)} components) and saved to products.csv")


if __name__ == "__main__":
    main()