import random
import ollama
import os
import subprocess
import csv
from datetime import datetime
import re
import tempfile
import shutil
import logging

# Logging konfigurieren
logging.basicConfig(
    filename='script.log',
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

# Funktion zum Einlesen der Anweisungen aus der Datei
def read_anweisungen(file_path):
    try:
        with open(file_path, 'r', encoding='utf-8') as file:
            content = file.read()
        # Anweisungen nach doppelten Leerzeilen trennen und strippen
        anweisungen = [anweisung.strip() for anweisung in content.split('\n\n') if anweisung.strip()]
        logging.info(f"Anweisungen aus '{file_path}' erfolgreich eingelesen.")
        return anweisungen
    except FileNotFoundError:
        logging.error(f"Die Datei '{file_path}' wurde nicht gefunden.")
        return []

# Funktion zum Speichern der Daten in die CSV-Datei mit DictWriter
def save_to_csv(file_path, date, begriffe, model, prompt):
    # Überprüfen, ob die Datei bereits existiert
    file_exists = os.path.isfile(file_path)

    try:
        with open(file_path, 'a', newline='', encoding='utf-8') as csvfile:
            fieldnames = ["Datum", "Begriffe", "Modell", "Prompt"]
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)

            # Wenn die Datei nicht existiert, Spaltenüberschriften hinzufügen
            if not file_exists:
                writer.writeheader()
                logging.info(f"Spaltenüberschriften in '{file_path}' hinzugefügt.")

            # Sonderzeichen und Zeilenumbrüche aus dem Prompt entfernen
            prompt = re.sub(r'[^\x00-\x7F]+||:', '', prompt)  # Entfernt nicht ASCII Zeichen und Doppelpunkte
            prompt = prompt.replace('\n', ' ').strip()  # Entfernt Zeilenumbrüche und führende Leerzeichen

            # Datenzeile schreiben
            writer.writerow({
                "Datum": date,
                "Begriffe": begriffe,
                "Modell": model,
                "Prompt": prompt
            })
            logging.info(f"Neue Zeile in '{file_path}' hinzugefügt.")
    except Exception as e:
        logging.error(f"Fehler beim Schreiben in '{file_path}': {e}")

# Funktion zur Abfrage der installierten Modelle über die Ollama CLI
def get_installed_models():
    try:
        result = subprocess.run(
            ['ollama', 'list'],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            check=True
        )
        lines = result.stdout.strip().split('\n')
        if len(lines) <= 1:
            logging.warning("Keine Modelle gefunden.")
            return {}  # Keine Modelle gefunden

        models = lines[1:]  # Überspringe die Kopfzeile
        model_dict = {}
        for i, model_line in enumerate(models):
            # Annahme: Der Modellname ist das erste Wort in der Zeile
            model_name = model_line.split()[0]
            model_dict[str(i + 1)] = model_name

        logging.info(f"{len(model_dict)} Modelle gefunden.")
        return model_dict
    except subprocess.CalledProcessError as e:
        logging.error(f"Fehler beim Abrufen der Modelle: {e.stderr}")
        return {}
    except Exception as e:
        logging.error(f"Unbekannter Fehler beim Abrufen der Modelle: {e}")
        return {}

# Funktion zum Anhängen des Prompts an prompt.txt
def append_to_prompt_txt(prompt, file_path='prompt.txt'):
    try:
        cleaned_prompt = prompt.strip()  # Entfernt führende und nachfolgende Leerzeichen
        with open(file_path, 'a', encoding='utf-8') as file:
            file.write(cleaned_prompt + '\n')
        logging.info(f"Prompt in '{file_path}' gespeichert.")
    except Exception as e:
        logging.error(f"Fehler beim Schreiben in '{file_path}': {e}")

# Funktion zur Validierung der Benutzereingabe für Begriffe
def get_valid_user_input(prompt_message):
    while True:
        user_input = input(prompt_message).strip()
        if user_input:
            # Weitere Validierungen können hier hinzugefügt werden
            if not user_input.isdigit():
                return user_input
            else:
                logging.warning("Die Eingabe darf keine reinen Zahlen sein.")
                print("Die Eingabe darf keine reinen Zahlen sein. Bitte versuche es erneut.")
        else:
            logging.warning("Leere Eingabe erkannt.")
            print("Die Eingabe darf nicht leer sein. Bitte versuche es erneut.")

# Funktion zur Bereinigung der CSV-Datei und Überschreiben der Originaldatei
def clean_csv(file_path):
    try:
        # Erstelle eine temporäre Datei
        with tempfile.NamedTemporaryFile(mode='w', delete=False, newline='', encoding='utf-8') as temp_file:
            temp_filename = temp_file.name
            with open(file_path, 'r', encoding='utf-8') as infile:
                reader = csv.DictReader(infile)
                fieldnames = reader.fieldnames
                if not fieldnames:
                    logging.error(f"Keine Feldnamen in der CSV-Datei '{file_path}' gefunden.")
                    return
                writer = csv.DictWriter(temp_file, fieldnames=fieldnames)

                # Schreibe die Kopfzeile
                writer.writeheader()
                logging.info(f"Spaltenüberschriften in temporärer Datei '{temp_filename}' hinzugefügt.")

                for row in reader:
                    # Überprüfen, ob 'Begriffe' keine unerwünschten Werte enthält
                    if row['Begriffe'].isdigit():
                        logging.warning(f"Überspringe Zeile mit ungültigen Begriffe: {row}")
                        continue  # Diese Zeile überspringen

                    # Bereinigen des 'Prompt'-Feldes
                    row['Prompt'] = row['Prompt'].strip().strip('"').rstrip(',')

                    writer.writerow(row)
                logging.info(f"Bereinigte Daten wurden in temporärer Datei '{temp_filename}' gespeichert.")

        # Ersetze die originale Datei durch die temporäre Datei
        shutil.move(temp_filename, file_path)  # Verwendung von shutil.move für bessere Plattformunterstützung
        logging.info(f"Die Datei '{file_path}' wurde erfolgreich aktualisiert.")
    except Exception as e:
        logging.error(f"Fehler bei der Bereinigung der CSV-Datei '{file_path}': {e}")

# Hauptprogramm
def main():
    anweisungen_file = 'anweisungen.txt'
    csv_file = 'prompts.csv'

    # Backup der CSV-Datei erstellen (optional, aber empfohlen)
    backup_file = 'prompts_backup.csv'
    try:
        if os.path.isfile(csv_file):
            shutil.copy(csv_file, backup_file)
            logging.info(f"Backup der CSV-Datei erstellt: '{backup_file}'")
            print(f"Backup der CSV-Datei wurde erstellt: '{backup_file}'")
        else:
            logging.warning(f"Die Datei '{csv_file}' existiert nicht und kann nicht gesichert werden.")
            print(f"Warnung: Die Datei '{csv_file}' existiert nicht und kann nicht gesichert werden.")
    except Exception as e:
        logging.error(f"Fehler beim Erstellen des Backups '{backup_file}': {e}")
        print(f"Fehler beim Erstellen des Backups '{backup_file}': {e}")

    # Einlesen der Anweisungen
    anweisungen = read_anweisungen(anweisungen_file)
    if not anweisungen:
        logging.error("Keine Anweisungen gefunden. Programm wird beendet.")
        print("Keine Anweisungen gefunden. Bitte überprüfe die Datei anweisungen.txt.")
        exit(1)

    # Zufällige Auswahl einer Anweisung
    selected_anweisung = random.choice(anweisungen)
    print(f"\nAusgewählte Anweisung: {selected_anweisung}")
    logging.info(f"Ausgewählte Anweisung: {selected_anweisung}")

    # Dynamisch installierte Modelle abrufen
    modelle = get_installed_models()

    # Überprüfen, ob Modelle verfügbar sind
    if not modelle:
        logging.error("Es sind keine Modelle installiert. Programm wird beendet.")
        print("Es sind keine Modelle installiert. Installiere bitte mindestens ein Modell.")
        exit(1)

    # Dem Benutzer die Modelle zur Auswahl anbieten
    print("\nVerfügbare Modelle:")
    logging.info("Zeige verfügbare Modelle an.")
    for key, model in modelle.items():
        print(f"Modell {key}: {model}")

    model_choice = input("\nDeine Wahl (Nummer): ").strip()

    selected_model = modelle.get(model_choice)
    if not selected_model:
        logging.error(f"Ungültige Modellwahl: '{model_choice}'. Programm wird beendet.")
        print("Ungültige Auswahl. Programm wird beendet.")
        exit(1)

    logging.info(f"Ausgewähltes Modell: {selected_model}")

    # Eingabe der Begriffe/Wörter durch den Benutzer mit Validierung
    user_input = get_valid_user_input("\nGib die Begriffe/Wörter ein: ")
    logging.info(f"Benutzereingabe Begriffe: {user_input}")

    # Initialisierung des Ollama-Clients
    try:
        client = ollama.Client()
        logging.info("Ollama-Client erfolgreich initialisiert.")
    except Exception as e:
        logging.error(f"Fehler beim Initialisieren des Ollama-Clients: {e}")
        print(f"Fehler beim Initialisieren des Ollama-Clients: {e}")
        exit(1)

    # Generierung des Textes mit dem ausgewählten Modell
    prompt = f"{selected_anweisung.strip()}\n{user_input.strip()}"

    logging.info(f"Generierter Prompt: {prompt}")

    try:
        response = client.generate(model=selected_model, prompt=prompt)
        logging.info("Textgenerierung erfolgreich.")
    except Exception as e:
        logging.error(f"Fehler bei der Generierung des Textes: {e}")
        print(f"Fehler bei der Generierung des Textes: {e}")
        exit(1)

    # Ausgabe und Verarbeitung der Antwort
    date = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    if 'response' in response:
        generated_text = response['response'].strip()
        print(f"\nGenerierte Antwort:\n{generated_text}")
        logging.info("Generierte Antwort erfolgreich erhalten.")

        # Speichern der Daten in die CSV-Datei
        save_to_csv(csv_file, date, user_input, selected_model, generated_text)
        logging.info("Daten wurden in die CSV-Datei gespeichert.")

        # Speichern des generierten Prompts in prompt.txt
        append_to_prompt_txt(generated_text)
        logging.info("Generierter Prompt wurde in 'prompt.txt' gespeichert.")
    else:
        logging.error("Fehler: Die Antwort enthält kein 'response'-Feld.")
        print("Fehler: Die Antwort enthält kein 'response'-Feld.")

    # Bereinigen der CSV-Datei nach dem Schreiben
    clean_csv(csv_file)

if __name__ == "__main__":
    main()
