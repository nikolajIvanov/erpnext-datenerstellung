import csv


def generate_top_level_group():
    return [
        {
            "Item Group Name": "Alle Artikelgruppen",
            "Image": "",
            "Is Group": 1,
            "old_parent": "",
            "Parent Item Group": "",
        }
    ]


def generate_second_level_groups():
    return [
        {
            "Item Group Name": "Produkte",
            "Image": "",
            "Is Group": 1,
            "old_parent": "",
            "Parent Item Group": "Alle Artikelgruppen",
        },
        {
            "Item Group Name": "Rohmaterial",
            "Image": "",
            "Is Group": 1,
            "old_parent": "",
            "Parent Item Group": "Alle Artikelgruppen",
        },
    ]


def generate_third_level_groups():
    return [
        {
            "Item Group Name": "Fahrräder",
            "Image": "",
            "Is Group": 0,
            "old_parent": "",
            "Parent Item Group": "Produkte",
        },
        {
            "Item Group Name": "E-Bikes",
            "Image": "",
            "Is Group": 0,
            "old_parent": "",
            "Parent Item Group": "Produkte",
        },
        {
            "Item Group Name": "Fahrradkomponenten",
            "Image": "",
            "Is Group": 0,
            "old_parent": "",
            "Parent Item Group": "Rohmaterial",
        },
        {
            "Item Group Name": "Dienstleistungen",
            "Image": "",
            "Is Group": 0,
            "old_parent": "",
            "Parent Item Group": "Alle Artikelgruppen",
        },
        {
            "Item Group Name": "Baugruppen",
            "Image": "",
            "Is Group": 0,
            "old_parent": "",
            "Parent Item Group": "Alle Artikelgruppen",
        },
        {
            "Item Group Name": "Verbrauchsmaterial",
            "Image": "",
            "Is Group": 0,
            "old_parent": "",
            "Parent Item Group": "Alle Artikelgruppen",
        },
    ]


def save_to_csv(item_groups, filename):
    fieldnames = [
        "Item Group Name", "Image", "Is Group", "old_parent", "Parent Item Group",
        "ID (Item Group Defaults)", "Company (Item Group Defaults)",
        "Default Buying Cost Center (Item Group Defaults)",
        "Default Discount Account (Item Group Defaults)",
        "Default Expense Account (Item Group Defaults)",
        "Default Income Account (Item Group Defaults)",
        "Default Price List (Item Group Defaults)",
        "Default Provisional Account (Item Group Defaults)",
        "Default Selling Cost Center (Item Group Defaults)",
        "Default Supplier (Item Group Defaults)",
        "Default Warehouse (Item Group Defaults)",
        "Deferred Expense Account (Item Group Defaults)",
        "Deferred Revenue Account (Item Group Defaults)",
        "ID (Taxes)", "Item Tax Template (Taxes)",
        "Maximum Net Rate (Taxes)", "Minimum Net Rate (Taxes)",
        "Tax Category (Taxes)", "Valid From (Taxes)"
    ]

    with open(filename, 'w', newline='', encoding='utf-8') as file:
        writer = csv.DictWriter(file, fieldnames=fieldnames)
        writer.writeheader()
        for group in item_groups:
            row = {field: "" for field in fieldnames}
            row.update(group)
            writer.writerow(row)


def main():
    top_level_group = generate_top_level_group()
    second_level_groups = generate_second_level_groups()
    third_level_groups = generate_third_level_groups()

    save_to_csv(top_level_group, '../Generated_CSV/1_top_level_item_group.csv')
    save_to_csv(second_level_groups, '../Generated_CSV/2_second_level_item_groups.csv')
    save_to_csv(third_level_groups, '../Generated_CSV/3_third_level_item_groups.csv')

    print("Top-Level Artikelgruppe wurde in '1_top_level_item_group.csv' gespeichert.")
    print("Zweite Ebene der Artikelgruppen wurde in '2_second_level_item_groups.csv' gespeichert.")
    print("Dritte Ebene der Artikelgruppen wurde in '3_third_level_item_groups.csv' gespeichert.")


if __name__ == "__main__":
    main()