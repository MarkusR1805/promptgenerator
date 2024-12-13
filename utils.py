import subprocess
import os
import csv
import re
import tempfile
import shutil
import logging
from datetime import datetime
import ollama

# Logging konfigurieren Logfile kreieren
logging.basicConfig(
    filename='script.log',
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

# Anweisungen.txt einlesen
def read_anweisungen(file_path):
    try:
        logging.info(f"Versuche, Anweisungen aus '{file_path}' zu lesen.")
        with open(file_path, 'r', encoding='utf-8') as file:
            content = file.read()
            anweisungen = [anweisung.strip() for anweisung in content.split('\n\n') if anweisung.strip()]
            logging.info(f"Anweisungen erfolgreich aus '{file_path}' eingelesen: {anweisungen}")
            return anweisungen
    except FileNotFoundError:
        logging.error(f"Die Datei '{file_path}' wurde nicht gefunden.")
        return []
    except Exception as e:
       logging.error(f"Ein Fehler trat beim Lesen der Datei auf: {e}")
       return []

# CSV-Datei speichern und formattieren
def save_to_csv(file_path, date, begriffe, model, prompt):
    file_exists = os.path.isfile(file_path)
    try:
        with open(file_path, 'a', newline='', encoding='utf-8') as csvfile:
            fieldnames = ["Datum", "Begriffe", "Modell", "Prompt"]
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            if not file_exists:
                writer.writeheader()
                logging.info(f"Spaltenüberschriften in '{file_path}' hinzugefügt.")
            prompt = prompt.strip()  # Entfernt führende und nachfolgende Leerzeichen
            if prompt.endswith('\n.'):
                prompt = prompt.replace('\n.', '').strip()
            prompt = prompt.replace('\n', ' ') # Zeilenumbrüche zu Leerzeichen
            prompt = re.sub(r'^\"', '', prompt) # Doppelte Anführungszeichen am Anfang entfernen
            prompt = re.sub(r'\"$', '', prompt) # Doppelte Anführungszeichen am Ende entfernen
            writer.writerow({
                "Datum": date,
                "Begriffe": begriffe,
                "Modell": model,
                "Prompt": prompt
            })
            logging.info(f"Neue Zeile in '{file_path}' hinzugefügt.")
    except Exception as e:
        logging.error(f"Fehler beim Schreiben in '{file_path}': {e}")

# Ollama list ausführen
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
            return {}
        models = lines[1:]
        model_dict = {str(i + 1): model_line.split()[0] for i, model_line in enumerate(models)}
        logging.info(f"{len(model_dict)} Modelle gefunden.")
        return model_dict
    except subprocess.CalledProcessError as e:
        logging.error(f"Fehler beim Abrufen der Modelle: {e.stderr}")
        return {}
    except Exception as e:
        logging.error(f"Unbekannter Fehler beim Abrufen der Modelle: {e}")
        return {}

# prompt.txt speichern
def append_to_prompt_txt(prompt, file_path='prompt.txt'):
    try:
        cleaned_prompt = prompt.strip()
        with open(file_path, 'a', encoding='utf-8') as file:
            file.write(cleaned_prompt + '\n')
        logging.info(f"Prompt in '{file_path}' gespeichert.")
    except Exception as e:
        logging.error(f"Fehler beim Schreiben in '{file_path}': {e}")

# CSV Prompts von " entfernen
def clean_csv(file_path):
    try:
        with tempfile.NamedTemporaryFile(mode='w', delete=False, newline='', encoding='utf-8') as temp_file:
            temp_filename = temp_file.name
            with open(file_path, 'r', encoding='utf-8') as infile:
                reader = csv.DictReader(infile)
                fieldnames = reader.fieldnames
                if not fieldnames:
                    logging.error(f"Keine Feldnamen in der CSV-Datei '{file_path}' gefunden.")
                    return
                writer = csv.DictWriter(temp_file, fieldnames=fieldnames)
                writer.writeheader()
                logging.info(f"Spaltenüberschriften in temporärer Datei '{temp_filename}' hinzugefügt.")
                for row in reader:
                    if row['Begriffe'].isdigit():
                        logging.warning(f"Überspringe Zeile mit ungültigen Begriffe: {row}")
                        continue
                    row['Prompt'] = row['Prompt'].strip().strip('"').rstrip(',')
                    row['Prompt'] = row['Prompt'].lstrip('"').rstrip('"') # Diese Zeile ergänzt
                    writer.writerow(row)
                logging.info(f"Bereinigte Daten wurden in temporärer Datei '{temp_filename}' gespeichert.")
        shutil.move(temp_filename, file_path)
        logging.info(f"Die Datei '{file_path}' wurde erfolgreich aktualisiert.")
    except Exception as e:
        logging.error(f"Fehler bei der Bereinigung der CSV-Datei '{file_path}': {e}")

def generate_ollama_prompt(selected_anweisung, user_input, selected_model):
    try:
        client = ollama.Client()
        prompt = f"{selected_anweisung.strip()}\n{user_input.strip()}"
        response = client.generate(model=selected_model, prompt=prompt)
        if 'response' in response:
           generated_text = response['response'].strip()
           generated_text = generated_text.strip()  # Entfernt führende und nachfolgende Leerzeichen
           if generated_text.endswith('\n.'):
                generated_text = generated_text.replace('\n.', '').strip()  # Entfernt die Zeile mit dem Punkt am Ende (bei manchen LLM's ein häufiges Vorkommen)
           generated_text = re.sub(r'^\"', '', generated_text) # Doppelte Anführungszeichen am Anfang entfernen
           generated_text = re.sub(r'\"$', '', generated_text) # Doppelte Anführungszeichen am Ende entfernen

           return generated_text
    except Exception as e:
        logging.error(f"Fehler bei der Generierung des Textes: {e}")
        return None
