import csv
from faker import Faker

# Initialize Faker for German locale
fake = Faker('de_DE')


def generate_territories():
    territories = [
        {
            "Territory Name": "Germany",
            "Is Group": 0,
            "Parent Territory": "All Territories",
            "Territory Manager": fake.name()
        },
        {
            "Territory Name": "Austria",
            "Is Group": 0,
            "Parent Territory": "All Territories",
            "Territory Manager": fake.name()
        },
        {
            "Territory Name": "Switzerland",
            "Is Group": 0,
            "Parent Territory": "All Territories",
            "Territory Manager": fake.name()
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
    territories = generate_territories()
    save_to_csv(territories, 'territories.csv')
    print(f"Generated {len(territories)} territories and saved to velo_gmbh_territories.csv")


if __name__ == "__main__":
    main()