import os


def write_directory_structure(root_dir, output_file, exclude_dirs=None):
    if exclude_dirs is None:
        exclude_dirs = []

    with open(output_file, 'w') as f:
        for dirpath, dirnames, filenames in os.walk(root_dir):
            # Verzeichnisse ignorieren, die ausgeschlossen werden sollen
            dirnames[:] = [d for d in dirnames if os.path.join(dirpath, d) not in exclude_dirs]

            # Erstelle den Pfad in der gewünschten Struktur
            level = dirpath.replace(root_dir, '').count(os.sep)
            indent = ' ' * 4 * level
            f.write(f"{indent}{os.path.basename(dirpath)}/\n")
            subindent = ' ' * 4 * (level + 1)
            for filename in filenames:
                f.write(f"{subindent}{filename}\n")


if __name__ == "__main__":
    # Hier das Verzeichnis einfügen, das du exportieren möchtest
    root_directory = os.path.dirname(os.path.abspath(__file__))  # Pfad zum Projektverzeichnis
    output_file = "../../folder_structure.txt"  # Name der Ausgabe-Datei

    # Verzeichnisse, die ausgeschlossen werden sollen
    exclude_directories = [
        os.path.join(root_directory, '.venv'),  # .venv-Verzeichnis ausschließen
        os.path.join(root_directory, '.git'),  # .git-Verzeichnis ausschließen
        os.path.join(root_directory, '.idea'),  # .idea-Verzeichnis ausschließen
        os.path.join(root_directory, '__pycache__'),  # __pycache__-Verzeichnisse ausschließen
    ]

    write_directory_structure(root_directory, output_file, exclude_dirs=exclude_directories)
    print(f"Ordnerstruktur wurde in {output_file} gespeichert, ohne die ausgeschlossenen Verzeichnisse.")