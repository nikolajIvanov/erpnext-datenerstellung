import csv
import random
from datetime import datetime, timedelta
import re

# Listen von typisch deutschen Vornamen, erweitert um die spezifischen Namen
male_names = {'Max', 'Felix', 'Paul', 'Leon', 'Lukas', 'Luca', 'Jonas', 'Maximilian', 'Julian', 'Elias', 'Finn', 'Noah',
              'Niklas', 'Jan', 'Tim', 'Tom', 'Moritz', 'David', 'Fabian', 'Simon', 'Erik', 'Alexander', 'Jakob',
              'Florian', 'Benjamin', 'Philipp', 'Nils', 'Michael', 'Daniel', 'Tobias', 'Christian', 'Kevin', 'Dennis',
              'Marco', 'Thomas', 'Peter', 'Andreas', 'Stefan', 'Martin', 'Hans', 'Jörg', 'Ralf', 'Uwe', 'Frank',
              'Klaus', 'Jürgen', 'Wolfgang', 'Dieter', 'Manfred', 'Heinz', 'Werner', 'Dimitri', 'Apostolos', 'Herbert',
              'Sören', 'Mato'}

female_names = {'Emma', 'Hanna', 'Hannah', 'Mia', 'Sofia', 'Sophia', 'Anna', 'Emilia', 'Lena', 'Marie', 'Leonie',
                'Sophie', 'Lina', 'Lea', 'Amelie', 'Clara', 'Klara', 'Nele', 'Luisa', 'Louisa', 'Laura', 'Lara', 'Maja',
                'Maya', 'Charlotte', 'Johanna', 'Sarah', 'Lisa', 'Julia', 'Maria', 'Katharina', 'Christina', 'Sandra',
                'Nicole', 'Melanie', 'Sabine', 'Petra', 'Monika', 'Karin', 'Ursula', 'Angelika', 'Renate', 'Helga',
                'Ingrid', 'Gertrud', 'Erika', 'Jolanda', 'Agatha', 'Irmingard', 'Hilma', 'Lieschen', 'Marzena',
                'Sophie', 'Johanne'}


def clean_name(name):
    # Ersetze Umlaute und ß
    umlaut_map = {
        'ä': 'ae', 'ö': 'oe', 'ü': 'ue', 'ß': 'ss',
        'Ä': 'Ae', 'Ö': 'Oe', 'Ü': 'Ue'
    }
    for umlaut, replacement in umlaut_map.items():
        name = name.replace(umlaut, replacement)

    # Entferne alle nicht-alphanumerischen Zeichen und ersetze Leerzeichen durch Punkte
    clean = re.sub(r'[^\w\s]', '', name)
    clean = clean.lower().replace(' ', '.')
    clean = re.sub(r'\.+', '.', clean)
    return clean.strip('.')


def determine_gender(first_name):
    first_name = first_name.split()[0]  # Nur der erste Teil des Vornamens
    if first_name in male_names:
        return "Male"
    elif first_name in female_names:
        return "Female"
    else:
        # Für unbekannte Namen: Zufällige Zuweisung mit Tendenz zu männlich (da oft in Vertriebspositionen)
        return random.choices(["Male", "Female"], weights=[0.7, 0.3])[0]


def read_sales_persons(filenames):
    sales_persons = []
    for filename in filenames:
        with open(filename, 'r', newline='', encoding='utf-8') as csvfile:
            reader = csv.DictReader(csvfile)
            sales_persons.extend(list(reader))
    return sales_persons


def generate_employee_data(sales_person, employee_id):
    full_name = sales_person['Sales Person Name']
    first_name, last_name = full_name.split(' ', 1)
    joining_date = (datetime.now() - timedelta(days=random.randint(30, 1825))).strftime("%Y-%m-%d")

    email = f"{clean_name(full_name)}@velo-gmbh.de"

    return {
        "ID": str(employee_id),
        "First Name": first_name,
        "Last Name": last_name,
        "Gender": determine_gender(first_name),
        "Date of Joining": joining_date,
        "Company": "Velo GmbH",
        "Department": "Sales",
        "Designation": "Sales Representative",
        "Status": "Active",
        "Company Email": email,
        "Mobile": f"+49{random.randint(1000000000, 9999999999)}",
        "Employee Number": f"S{employee_id:04d}",
        "Date of Birth": (datetime.now() - timedelta(days=random.randint(8030, 18250))).strftime("%Y-%m-%d"),
        "Reports to": "",  # This will be filled later
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
        "Role Profile": "Sales",
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
    sales_files = ['../master/sales_directors.csv',
                   '../master/sales_managers.csv',
                   '../master/sales_reps.csv']
    sales_persons = read_sales_persons(sales_files)

    # Create a mapping of names to IDs and a hierarchy dictionary
    name_to_id = {}
    hierarchy = {}
    for i, sp in enumerate(sales_persons, start=3):  # Start from 3 as CEO is 1 and COO is 2
        employee_id = i
        name_to_id[sp['Sales Person Name']] = employee_id
        parent = sp.get('Parent Sales Person', '')
        if parent not in hierarchy:
            hierarchy[parent] = []
        hierarchy[parent].append(sp)

    employee_fields = [
        "ID", "First Name", "Last Name", "Gender", "Date of Joining", "Company",
        "Department", "Designation", "Status", "Company Email", "Mobile",
        "Employee Number", "Date of Birth", "Reports to"
    ]

    user_fields = [
        "ID", "Email", "First Name", "Last Name", "Full Name", "Username",
        "Gender", "Enabled", "Role Profile", "User Type", "Language"
    ]

    # Process sales persons level by level
    level = 0
    to_process = ['']  # Start with the top level (no parent)
    all_employees = []
    all_users = []

    while to_process:
        employees = []
        users = []
        next_level = []
        for parent in to_process:
            for sp in hierarchy.get(parent, []):
                employee_id = name_to_id[sp['Sales Person Name']]
                employee = generate_employee_data(sp, employee_id)
                if level == 0:
                    employee['Reports to'] = "2"  # Sales Director reports to COO (ID 2)
                else:
                    employee['Reports to'] = str(name_to_id.get(sp['Parent Sales Person'],
                                                                '3'))  # Default to Sales Director (ID 3) if parent not found
                employees.append(employee)
                users.append(generate_user_data(employee))
                next_level.append(sp['Sales Person Name'])

        all_employees.extend(employees)
        all_users.extend(users)

        if employees:
            write_to_csv(employees, f'../generated/employees_level_{level}.csv', employee_fields)
            write_to_csv(users, f'../generated/users_level_{level}.csv', user_fields)
            print(f"Generated {len(employees)} employees for level {level}")
            print(f"Please import 'employees_level_{level}.csv' and 'users_level_{level}.csv' now.")
            input("Press Enter when you have completed the import for this level...")
        else:
            print(f"No employees found for level {level}")

        level += 1
        to_process = next_level

    # Write all employees and users to single files
    write_to_csv(all_employees, '../generated/all_employees.csv', employee_fields)
    write_to_csv(all_users, '../generated/all_users.csv', user_fields)
    print("Generated files for all employees and users: 'all_employees.csv' and 'all_users.csv'")


if __name__ == "__main__":
    main()
