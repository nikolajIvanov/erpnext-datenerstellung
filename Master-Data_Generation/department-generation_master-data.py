import csv

"""
Diese Datei dient dazu neue Departments zu erstellen. Im aktuellen Case wird diese Datei erstmal nicht benötigt.
"""


def generate_departments():
    new_departments = [
        {
            "ID": "Business Development",
            "Company": "Bikeshop",
            "Department": "Business Development",
            "Disabled": 0,
            "Is Group": 0,
            "Parent Department": "All Departments"
        },
        # Add more departments here if needed
    ]
    return new_departments


def save_to_csv(departments, filename):
    fieldnames = [
        "ID", "Company", "Department", "Disabled", "Is Group", "Old Parent", "Parent Department"
    ]

    with open(filename, 'w', newline='', encoding='utf-8') as output_file:
        writer = csv.DictWriter(output_file, fieldnames=fieldnames)
        writer.writeheader()
        for dept in departments:
            writer.writerow(dept)


def main():
    new_departments = generate_departments()
    save_to_csv(new_departments, '../Generated_CSV/departments.csv')
    print(f"Generated {len(new_departments)} new departments and saved to departments.csv")


if __name__ == "__main__":
    main()
