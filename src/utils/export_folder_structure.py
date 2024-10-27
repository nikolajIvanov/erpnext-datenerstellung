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
    # Ermittle das Basis-Verzeichnis (2 Ebenen höher als die aktuelle Datei)
    current_dir = os.path.dirname(os.path.abspath(__file__))
    root_directory = os.path.dirname(os.path.dirname(current_dir))

    # Ausgabedatei im Basis-Verzeichnis
    output_file = os.path.join(root_directory, "folder_structure.txt")

    # Verzeichnisse, die ausgeschlossen werden sollen
    exclude_directories = [
        os.path.join(root_directory, '.venv'),
        os.path.join(root_directory, '.git'),
        os.path.join(root_directory, '.idea'),
        os.path.join(root_directory, '__pycache__'),
    ]

    write_directory_structure(root_directory, output_file, exclude_dirs=exclude_directories)
    print(f"Ordnerstruktur wurde in {output_file} gespeichert, ohne die ausgeschlossenen Verzeichnisse.")