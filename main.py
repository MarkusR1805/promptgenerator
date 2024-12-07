import sys
import random
import subprocess
import os
import csv
from datetime import datetime
import re
import tempfile
import shutil
import logging
from PyQt6.QtWidgets import QApplication, QWidget, QVBoxLayout, QPushButton, QLabel, QLineEdit, QTextEdit, QComboBox, QMessageBox, QDialog, QDialogButtonBox, QMainWindow, QSizePolicy
from PyQt6.QtGui import QClipboard, QScreen, QFont, QPixmap
from PyQt6.QtCore import QTimer, Qt
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
            prompt = re.sub(r'[^\x00-\x7F]+||:', '', prompt)
            prompt = prompt.replace('\n', ' ').strip()
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
                    writer.writerow(row)
                logging.info(f"Bereinigte Daten wurden in temporärer Datei '{temp_filename}' gespeichert.")
        shutil.move(temp_filename, file_path)
        logging.info(f"Die Datei '{file_path}' wurde erfolgreich aktualisiert.")
    except Exception as e:
        logging.error(f"Fehler bei der Bereinigung der CSV-Datei '{file_path}': {e}")

# Dialogfenster nach dem generieren
class PromptEditDialog(QDialog):
    def __init__(self, prompt):
        super().__init__()
        self.setWindowTitle("Prompt bearbeiten / Edit promptly")
        self.prompt = prompt
        self.initUI()

        # Schriftart und -größe festlegen
        font = QFont()
        font.setPointSize(16)
        self.setFont(font)

    # ANCHOR Bearbeiten Dialog
    def initUI(self):
        self.setFixedSize(500,300)
        layout = QVBoxLayout()
        self.text_edit = QTextEdit()
        self.text_edit.setPlainText(self.prompt)
        layout.addWidget(self.text_edit)

        button_box = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel)
        button_box.accepted.connect(self.accept)
        button_box.rejected.connect(self.reject)
        layout.addWidget(button_box)
        self.setLayout(layout)

    def get_edited_prompt(self):
        return self.text_edit.toPlainText()

class App(QWidget):
    def __init__(self):
        super().__init__()
        self.initUI()

        # Schriftart und -größe festlegen
        font = QFont()
        font.setPointSize(14)
        self.setFont(font)

    # ANCHOR Titel
    def initUI(self):
        self.setWindowTitle('2024 / Promptgenerator 2.3.1 | by Der Zerfleischer on ')
        # self.setGeometry(100, 100, 600, 600)  # Angepasste Fensterbreite
        # self.setFixedSize(self.size())
        self.setFixedSize(600, 600)

        layout = QVBoxLayout()

        self.anweisungen_label = QLabel('Anweisungen:')
        layout.addWidget(self.anweisungen_label)

        self.anweisungen_combo = QComboBox()
        self.anweisungen_combo.setMinimumHeight(25)  # Höhe für zweizeilige Anzeige
        self.anweisungen_combo.setSizePolicy(QSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred))  # Korrektur hier
        self.anweisungen_combo.setMaximumWidth(600) # Maximale Breite hinzugefügt
        self.load_anweisungen()
        layout.addWidget(self.anweisungen_combo)


        self.model_label = QLabel('Modell:')
        layout.addWidget(self.model_label)

        self.model_combo = QComboBox()
        self.load_models()
        layout.addWidget(self.model_combo)

        self.begriffe_label = QLabel('Begriffe / Keywords:')
        layout.addWidget(self.begriffe_label)

        self.begriffe_input = QTextEdit()  # Mehrzeiliges Eingabefeld
        self.begriffe_input.setMaximumHeight(100)  # Maximale Höhe, damit es nicht zu gross wird
        layout.addWidget(self.begriffe_input)


        self.generate_button = QPushButton('Generieren / Generate')
        self.generate_button.clicked.connect(self.generate_text)
        layout.addWidget(self.generate_button)


        self.generated_text_label = QLabel('Generierter Prompt / Generate prompt:')
        layout.addWidget(self.generated_text_label)
        # Anchor Textfeldgröße
        self.generated_text_edit = QTextEdit()
        self.generated_text_edit.setMinimumSize(0,100)
        layout.addWidget(self.generated_text_edit)

        self.copy_to_clipboard_button = QPushButton('In Zwischenablage kopieren / Copy to clipboard')
        self.copy_to_clipboard_button.clicked.connect(self.copy_to_clipboard)
        layout.addWidget(self.copy_to_clipboard_button)


        # ANCHOR Bild-Label erstellen und zentrieren
        self.image_label = QLabel()
        self.set_image("bild.png") # hier kommt der Name des Bildes rein
        self.image_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self.image_label)

        self.setLayout(layout)

        # Erste Anweisung beim Start auswählen
        if self.anweisungen_combo.count() > 0:
            self.anweisungen_combo.setCurrentIndex(0)

    def set_image(self, image_path):
         try:
            pixmap = QPixmap(image_path)
            if pixmap.isNull():
               logging.error(f"Fehler: Bild '{image_path}' konnte nicht geladen werden.")
            else:
               self.image_label.setPixmap(pixmap.scaled(300, 100, Qt.AspectRatioMode.KeepAspectRatio)) #Anpassung der Größe
         except Exception as e:
               logging.error(f"Fehler beim setzen des Bildes: {e}")

    def load_anweisungen(self):
        anweisungen = read_anweisungen('anweisungen.txt')
        if anweisungen:
            self.anweisungen_combo.addItems(anweisungen)
            # ab hier teste ich etwas
            font_metrics = self.anweisungen_combo.fontMetrics()
            max_width = 0
            for anweisung in anweisungen:
                width = font_metrics.horizontalAdvance(anweisung)
                max_width = max(max_width, width)
            max_width = min(max_width + 20, 600) # 20px für Padding, maximal 500px
            self.anweisungen_combo.setMaximumWidth(max_width)
            # hier test ende
        else:
            QMessageBox.critical(self, 'Fehler', 'Keine Anweisungen gefunden. Bitte überprüfe die Datei anweisungen.txt.\nNo instructions found. Please check the file anweisungen.txt.')

    def load_models(self):
        models = get_installed_models()
        if models:
            self.model_combo.addItems([f"Modell {k}: {v}" for k, v in models.items()])
        else:
            QMessageBox.critical(self, 'Fehler', 'Es sind keine Modelle installiert. Installiere bitte mindestens ein Modell.\nNo models are installed. Please install at least one model.')

    def generate_text(self):
        selected_anweisung = self.anweisungen_combo.currentText()
        selected_model = self.model_combo.currentText().split(': ')[1]
        user_input = self.begriffe_input.toPlainText().strip() # Änderung von text() zu toPlainText() für QTextEdit

        if not user_input:
            QMessageBox.warning(self, 'Fehler', 'Die Eingabe darf nicht leer sein.\nThe input must not be empty')
            return

        try:
            client = ollama.Client()
            prompt = f"{selected_anweisung.strip()}\n{user_input.strip()}"
            response = client.generate(model=selected_model, prompt=prompt)
            if 'response' in response:
                generated_text = response['response'].strip()
                self.generated_text_edit.setPlainText(generated_text)

                dlg = PromptEditDialog(generated_text)
            if dlg.exec():
                edited_prompt = dlg.get_edited_prompt()
                self.generated_text_edit.setPlainText(edited_prompt)  # Hier wird der bearbeitete Prompt im Hauptfenster aktualisiert
                date = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                save_to_csv('prompts.csv', date, user_input, selected_model, edited_prompt)
                append_to_prompt_txt(edited_prompt)
                clean_csv('prompts.csv')
            else:
                #QMessageBox.critical(self, 'Fehler', 'Die Antwort enthält kein \'response\'-Feld.')
                QMessageBox.critical(self, 'Fehler', 'Prompt wird nicht gespeichert!\nPrompt not saved!')
        except Exception as e:
            QMessageBox.critical(self, 'Fehler', f'Fehler bei der Generierung des Textes: {e}')

    def copy_to_clipboard(self):
        generated_text = self.generated_text_edit.toPlainText()
        if generated_text:
            clipboard = QApplication.clipboard()
            clipboard.setText(generated_text)

            # Ändere die Hintergrundfarbe des Buttons
            self.copy_to_clipboard_button.setStyleSheet("background-color: green")

            # Erstelle einen Timer, um die Farbe nach 500 ms zurückzusetzen
            QTimer.singleShot(500, self.reset_button_color)
        else:
            QMessageBox.warning(self, 'Fehler', 'Es gibt keinen generierten Text, der in die Zwischenablage kopiert werden kann.\nThere is no generated text that can be copied to the clipboard.')

    def reset_button_color(self):
        # Setzt die Hintergrundfarbe des Buttons zurück
        self.copy_to_clipboard_button.setStyleSheet("")

if __name__ == '__main__':
    app = QApplication(sys.argv)
    ex = App()
    ex.show()
    sys.exit(app.exec())
