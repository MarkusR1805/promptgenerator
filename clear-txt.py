import os

def process_file(file_path):
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            lines = f.readlines()

        processed_entries = set()
        for line in lines:
            # Konvertiere zu Kleinbuchstaben
            entry = line.lower()

            # Entferne führende Leerzeichen
            entry = entry.lstrip()

            # Entferne nachgestellte Leerzeichen und Zeilenumbrüche
            entry = entry.rstrip()

            # Entferne Komma am Ende, falls vorhanden
            if entry.endswith(','):
                entry = entry[:-1]

            # Stelle sicher, dass der Eintrag mit einem Punkt endet
            if not entry.endswith('.'):
                entry = entry.rstrip('.') + '.'

            # Füge den Eintrag zur Menge hinzu (entfernt Duplikate)
            processed_entries.add(entry)

        # Sortiere die Einträge alphabetisch
        sorted_entries = sorted(processed_entries)

        # Schreibe die Ergebnisse in die Originaldatei (Überschreiben)
        with open(file_path, 'w', encoding='utf-8') as f:
            for entry in sorted_entries:
                f.write(entry + '\n')

        print(f"Die Datei '{file_path}' wurde erfolgreich verarbeitet und überschrieben.")

    except FileNotFoundError:
        print(f"Die Datei '{file_path}' wurde nicht gefunden. Bitte überprüfen Sie den Pfad.")
    except PermissionError:
        print(f"Es fehlen die erforderlichen Berechtigungen, um die Datei '{file_path}' zu bearbeiten.")
    except Exception as e:
        print(f"Ein Fehler ist aufgetreten: {e}")

if __name__ == "__main__":
    while True:
        file_path = input("Bitte den Pfad zur Datei angeben: ")
        if not os.path.isfile(file_path):
            print(f"Die Datei '{file_path}' wurde nicht gefunden. Bitte geben Sie einen gültigen Pfad ein.")
        else:
            process_file(file_path)
            break