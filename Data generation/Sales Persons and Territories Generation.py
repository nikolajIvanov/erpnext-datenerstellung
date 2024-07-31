import csv
from faker import Faker

"""
OBSOLET
"""
# Initialize Faker for German locale
fake = Faker('de_DE')


def generate_sales_structure():
    territories = ["Germany", "Austria", "Switzerland"]
    sales_structure = []
    territory_data = []

    # Create a top-level sales director
    sales_director = {
        "Sales Person Name": fake.name(),
        "Is Group": 1,
        "Commission Rate": round(fake.random.uniform(7, 9), 2),
        "Department": "Sales",
        "Employee": "",
        "Enabled": 1,
        "Parent Sales Person": "",
        "Position": "Sales Director"
    }
    sales_structure.append(sales_director)

    for territory in territories:
        # Generate one Regional Sales Manager for each territory
        regional_manager = {
            "Sales Person Name": fake.name(),
            "Is Group": 1,
            "Commission Rate": round(fake.random.uniform(5, 7), 2),
            "Department": "Sales",
            "Employee": "",
            "Enabled": 1,
            "Parent Sales Person": sales_director["Sales Person Name"],
            "Position": f"Regional Sales Manager - {territory}"
        }
        sales_structure.append(regional_manager)

        # Generate Territory data
        territory_info = {
            "Territory Name": territory,
            "Is Group": 0,
            "Parent Territory": "All Territories",
            "Territory Manager": regional_manager["Sales Person Name"]
        }
        territory_data.append(territory_info)

        # Generate 3 Sales Representatives for each territory
        for _ in range(3):
            sales_rep = {
                "Sales Person Name": fake.name(),
                "Is Group": 0,
                "Commission Rate": round(fake.random.uniform(1, 3), 2),
                "Department": "Sales",
                "Employee": "",
                "Enabled": 1,
                "Parent Sales Person": regional_manager["Sales Person Name"],
                "Position": f"Sales Representative - {territory}"
            }
            sales_structure.append(sales_rep)

    return sales_structure, territory_data


def save_to_csv(data, filename, fieldnames):
    with open(filename, 'w', newline='', encoding='utf-8') as output_file:
        writer = csv.DictWriter(output_file, fieldnames=fieldnames)
        writer.writeheader()
        for item in data:
            # Fill in empty values for fields not generated
            for field in fieldnames:
                if field not in item:
                    item[field] = ""
            writer.writerow(item)


def main():
    sales_person_fields = [
        "Sales Person Name", "Is Group", "Commission Rate", "Department",
        "Employee", "Enabled", "old_parent", "Parent Sales Person",
        "Position",  # Added this field to show the role
        "ID (Targets)", "Fiscal Year (Targets)", "Item Group (Targets)",
        "Target  Amount (Targets)", "Target Distribution (Targets)", "Target Qty (Targets)"
    ]

    territory_fields = [
        "Territory Name", "Is Group", "old_parent", "Parent Territory",
        "Territory Manager", "ID (Targets)", "Fiscal Year (Targets)",
        "Item Group (Targets)", "Target  Amount (Targets)",
        "Target Distribution (Targets)", "Target Qty (Targets)"
    ]

    sales_structure, territories = generate_sales_structure()

    save_to_csv(sales_structure, 'velo_gmbh_sales_structure.csv', sales_person_fields)
    save_to_csv(territories, 'velo_gmbh_territories.csv', territory_fields)

    print(f"Generated {len(sales_structure)} sales persons and saved to velo_gmbh_sales_structure.csv")
    print(f"Generated {len(territories)} territories and saved to velo_gmbh_territories.csv")


if __name__ == "__main__":
    main()