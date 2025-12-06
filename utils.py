# utils.py
import subprocess
import os
import csv
import re
import tempfile
import shutil
import logging
from datetime import datetime
import ollama

# Logging wird erst später initialisiert → keine Konfiguration hier!
_logger_configured = False

def setup_logging(log_file_path):
    """Initialisiert das Logging mit einem benutzerspezifischen Pfad."""
    global _logger_configured
    if not _logger_configured:
        logging.basicConfig(
            filename=log_file_path,
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s',
            force=True
        )
        _logger_configured = True


def read_anweisungen(file_path):
    try:
        logging.info(f"Versuche, Anweisungen aus '{file_path}' zu lesen.")
        with open(file_path, 'r', encoding='utf-8') as file:
            content = file.read()
            anweisungen = [anweisung.strip() for anweisung in content.split('\n\n') if anweisung.strip()]
            logging.info(f"Anweisungen erfolgreich eingelesen: {anweisungen}")
            return anweisungen
    except FileNotFoundError:
        logging.error(f"Die Datei '{file_path}' wurde nicht gefunden.")
        return []
    except Exception as e:
        logging.error(f"Ein Fehler trat beim Lesen der Datei auf: {e}")
        return []


def save_to_csv(file_path, date, begriffe, model, prompt):
    file_exists = os.path.isfile(file_path)
    try:
        with open(file_path, 'a', newline='', encoding='utf-8') as csvfile:
            fieldnames = ["Datum", "Begriffe", "Modell", "Prompt"]
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            if not file_exists:
                writer.writeheader()
                logging.info(f"Spaltenüberschriften in '{file_path}' hinzugefügt.")
            prompt = prompt.strip()
            if prompt.endswith('\n.'):
                prompt = prompt.replace('\n.', '').strip()
            prompt = prompt.replace('\n', ' ')
            prompt = re.sub(r'^\"', '', prompt)
            prompt = re.sub(r'\"$', '', prompt)
            writer.writerow({
                "Datum": date,
                "Begriffe": begriffe,
                "Modell": model,
                "Prompt": prompt
            })
            logging.info(f"Neue Zeile in '{file_path}' hinzugefügt.")
    except Exception as e:
        logging.error(f"Fehler beim Schreiben in '{file_path}': {e}")


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


def append_to_prompt_txt(prompt, file_path):
    """Speichert den Prompt in eine benutzerspezifische Datei (nicht mehr mit Default-Wert!)."""
    try:
        cleaned_prompt = prompt.strip()
        with open(file_path, 'a', encoding='utf-8') as file:
            file.write(cleaned_prompt + '\n')
        logging.info(f"Prompt in '{file_path}' gespeichert.")
    except Exception as e:
        logging.error(f"Fehler beim Schreiben in '{file_path}': {e}")


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
                for row in reader:
                    if row['Begriffe'].isdigit():
                        logging.warning(f"Überspringe Zeile mit ungültigen Begriffen: {row}")
                        continue
                    row['Prompt'] = row['Prompt'].strip().strip('"').rstrip(',')
                    row['Prompt'] = row['Prompt'].lstrip('"').rstrip('"')
                    writer.writerow(row)
            logging.info(f"Bereinigte Daten in temporärer Datei gespeichert.")
        shutil.move(temp_filename, file_path)
        logging.info(f"Datei '{file_path}' erfolgreich aktualisiert.")
    except Exception as e:
        logging.error(f"Fehler bei der Bereinigung der CSV-Datei '{file_path}': {e}")


def generate_ollama_prompt(selected_anweisung, user_input, selected_model):
    try:
        client = ollama.Client()
        prompt = f"{selected_anweisung.strip()}\n{user_input.strip()}"
        response = client.generate(model=selected_model, prompt=prompt)
        if 'response' in response:
            generated_text = response['response'].strip()
            if generated_text.endswith('\n.'):
                generated_text = generated_text.replace('\n.', '').strip()
            generated_text = re.sub(r'^\"', '', generated_text)
            generated_text = re.sub(r'\"$', '', generated_text)
            return generated_text
    except Exception as e:
        logging.error(f"Fehler bei der Generierung des Textes: {e}")
        return None
