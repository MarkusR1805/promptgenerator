# utils.py
import subprocess
import os
import csv
import re
import tempfile
import shutil
import logging
from datetime import datetime

def find_ollama_binary():
    """Findet den ollama-Befehl – auch ohne PATH."""
    candidates = [
        "/usr/local/bin/ollama",
        "/opt/homebrew/bin/ollama",
        os.path.expanduser("~/.ollama/bin/ollama")
    ]
    for path in candidates:
        if os.path.isfile(path):
            return path
    import shutil
    return shutil.which("ollama")

# Logging
_logger_configured = False

def setup_logging(log_file_path):
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
    ollama_cmd = find_ollama_binary()
    if not ollama_cmd:
        logging.error("Ollama-CLI nicht gefunden.")
        return {}

    try:
        result = subprocess.run(
            [ollama_cmd, 'list'],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            check=True,
            timeout=30
        )
        lines = result.stdout.strip().split('\n')
        if len(lines) <= 1:
            logging.warning("Keine Modelle gefunden.")
            return {}
        models = lines[1:]
        model_dict = {str(i + 1): model_line.split()[0] for i, model_line in enumerate(models)}
        logging.info(f"{len(model_dict)} Modelle gefunden.")
        return model_dict
    except subprocess.TimeoutExpired:
        logging.error("Timeout beim Abrufen der Modelle.")
        return {}
    except subprocess.CalledProcessError as e:
        logging.error(f"Fehler beim Abrufen der Modelle: {e.stderr}")
        return {}
    except Exception as e:
        logging.error(f"Unbekannter Fehler beim Abrufen der Modelle: {e}")
        return {}

def append_to_prompt_txt(prompt, file_path):
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
    ollama_cmd = find_ollama_binary()
    if not ollama_cmd:
        logging.error("Ollama-CLI nicht gefunden.")
        return None

    try:
        prompt_text = f"{selected_anweisung.strip()}\n{user_input.strip()}"
        result = subprocess.run(
            [ollama_cmd, "run", selected_model, prompt_text],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            timeout=120
        )
        if result.returncode == 0:
            generated_text = result.stdout.strip()
            if generated_text.endswith('\n.'):
                generated_text = generated_text.replace('\n.', '').strip()
            generated_text = re.sub(r'^\"', '', generated_text)
            generated_text = re.sub(r'\"$', '', generated_text)
            return generated_text
        else:
            logging.error(f"Ollama-Fehler: {result.stderr}")
            return None
    except subprocess.TimeoutExpired:
        logging.error("Ollama-Timeout bei der Generierung.")
        return None
    except Exception as e:
        logging.error(f"Unerwarteter Fehler: {e}")
        return None
