import csv
import random
from datetime import datetime, timedelta


def generate_ceo_data(name, designation):
    first_name, last_name = name.split(' ', 1)
    joining_date = (datetime.now() - timedelta(days=random.randint(365, 3650))).strftime("%Y-%m-%d")
    return {
        "ID": f"EMP-CEO-{random.randint(1000, 9999)}",
        "First Name": first_name,
        "Last Name": last_name,
        "Gender": random.choice(["Male", "Female"]),
        "Date of Joining": joining_date,
        "Company": "Velo GmbH",
        "Department": "Management",
        "Designation": designation,
        "Status": "Active",
        "Company Email": f"{first_name.lower()}.{last_name.lower()}@velo-gmbh.de",
        "Mobile": f"+49{random.randint(1000000000, 9999999999)}",
        "Employee Number": f"CEO{random.randint(1000, 9999)}",
        "Date of Birth": (datetime.now() - timedelta(days=random.randint(18250, 23725))).strftime("%Y-%m-%d"),
        "Reports to": "",
    }


def generate_user_data(employee):
    return {
        "ID": employee['Company Email'],
        "Email": employee['Company Email'],
        "First Name": employee['First Name'],
        "Last Name": employee['Last Name'],
        "Full Name": f"{employee['First Name']} {employee['Last Name']}",
        "Username": employee['Company Email'].split('@')[0],
        "Gender": employee['Gender'],
        "Enabled": 1,
        "Role Profile": "CEO",
        "User Type": "System User",
        "Language": "de",
    }


def write_to_csv(data, filename, fieldnames):
    with open(filename, 'w', newline='', encoding='utf-8') as csvfile:
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        writer.writeheader()
        for row in data:
            writer.writerow(row)


def main():
    ceos = [
        generate_ceo_data("Max Mustermann", "Chief Executive Officer"),
        generate_ceo_data("Erika Musterfrau", "Chief Operating Officer")
    ]

    users = [generate_user_data(ceo) for ceo in ceos]

    employee_fields = [
        "ID", "First Name", "Last Name", "Gender", "Date of Joining", "Company",
        "Department", "Designation", "Status", "Company Email", "Mobile",
        "Employee Number", "Date of Birth", "Reports to"
    ]

    user_fields = [
        "ID", "Email", "First Name", "Last Name", "Full Name", "Username",
        "Gender", "Enabled", "Role Profile", "User Type", "Language"
    ]

    write_to_csv(ceos, '../generated/ceos_employee.csv', employee_fields)
    write_to_csv(users, '../generated/ceo_users.csv', user_fields)


if __name__ == "__main__":
    main()
