# main.py

__version__ = '2.5.0'

import sys
import os
from pathlib import Path
from datetime import datetime
from PySide6.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QPushButton, QLabel, QTextEdit, QComboBox,
    QMessageBox, QDialog, QDialogButtonBox, QSizePolicy
)
from PySide6.QtGui import QClipboard, QFont
from PySide6.QtCore import QTimer

# Import aus utils – ACHTUNG: Logging wird erst nach Pfadinitialisierung eingerichtet!
from utils import read_anweisungen, get_installed_models, save_to_csv, append_to_prompt_txt, clean_csv, generate_ollama_prompt, setup_logging

# ===== Pfad-Logik für Nuitka + macOS App Bundle =====
def get_resource_path(relative_path):
    """Gibt den Pfad zu einer mitgelieferten Ressource zurück (z.B. anweisungen.txt)."""
    if sys.platform == "darwin" and getattr(sys, "frozen", False):
        # Nuitka: sys.executable ist .../Promptgenerator.app/Contents/MacOS/main
        bundle_resources = Path(sys.executable).parent.parent / "Resources"
        return str(bundle_resources / relative_path)
    else:
        # Entwicklungsumgebung
        return str(Path(__file__).parent / relative_path)

# Lesbare Ressource (im Bundle oder Projektordner)
ANWEISUNGEN_FILE = get_resource_path("anweisungen.txt")

# Schreibbare Daten → Desktop/Promptgenerator
DATA_DIR = Path.home() / "Desktop" / "Promptgenerator"
DATA_DIR.mkdir(exist_ok=True)
PROMPTS_CSV = DATA_DIR / "prompts.csv"
PROMPT_TXT = DATA_DIR / "prompt.txt"
LOG_FILE = DATA_DIR / "script.log"

# Logging aktivieren (vor QApplication!)
setup_logging(str(LOG_FILE))

# Schriftgröße
FONT_SIZE = 16


# ===== GUI-Klassen =====
class PromptEditDialog(QDialog):
    def __init__(self, prompt):
        super().__init__()
        self.setWindowTitle("Prompt bearbeiten / Edit promptly")
        self.prompt = prompt
        self.initUI()

        font = QFont()
        font.setPointSize(FONT_SIZE)
        self.setFont(font)

    def initUI(self):
        self.setFixedSize(600, 400)
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

        font = QFont()
        font.setPointSize(FONT_SIZE)
        self.setFont(font)

    def initUI(self):
        self.setWindowTitle(f'2025 / Promptgenerator ({__version__}) 🍎')
        self.setFixedSize(800, 600)

        layout = QVBoxLayout()

        self.anweisungen_label = QLabel('Anweisungen / Instruction:')
        layout.addWidget(self.anweisungen_label)

        self.anweisungen_combo = QComboBox()
        self.anweisungen_combo.setMinimumHeight(25)
        self.anweisungen_combo.setToolTip("Anweisung auswählen.")
        self.anweisungen_combo.setSizePolicy(QSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred))
        self.load_anweisungen()
        layout.addWidget(self.anweisungen_combo)

        self.model_label = QLabel('Ollama Modelle / Ollama models:')
        layout.addWidget(self.model_label)

        self.model_combo = QComboBox()
        self.model_combo.setMinimumHeight(25)
        self.model_combo.setToolTip("Modell auswählen.")
        self.model_combo.setSizePolicy(QSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred))
        self.load_models()
        layout.addWidget(self.model_combo)

        self.begriffe_label = QLabel('Begriffe / Keywords:')
        layout.addWidget(self.begriffe_label)

        self.begriffe_input = QTextEdit()
        self.begriffe_input.setMaximumHeight(70)
        self.begriffe_input.setToolTip("Geben Sie hier die Begriffe ein, die im Prompt verwendet werden sollen.")
        layout.addWidget(self.begriffe_input)

        self.generate_button = QPushButton('Generieren / Generate')
        self.generate_button.clicked.connect(self.generate_text)
        self.generate_button.setToolTip("Start des Prozezesses.")
        layout.addWidget(self.generate_button)

        self.generated_text_label = QLabel('Generierter Prompt / Generate prompt:')
        layout.addWidget(self.generated_text_label)

        self.generated_text_edit = QTextEdit()
        self.generated_text_edit.setMinimumSize(0, 70)
        self.generated_text_edit.setToolTip("Der generierte Prompt aus den vorgegebenen Schlagwörtern.")
        layout.addWidget(self.generated_text_edit)

        self.copy_to_clipboard_button = QPushButton('In Zwischenablage kopieren / Copy to clipboard')
        self.copy_to_clipboard_button.clicked.connect(self.copy_to_clipboard)
        self.copy_to_clipboard_button.setToolTip("Der generierte Prompt in die Zwischenablage kopieren.")
        self.copy_to_clipboard_button.setFont(QFont('', FONT_SIZE))
        layout.addWidget(self.copy_to_clipboard_button)

        self.quit_button = QPushButton('Beenden / Quit')
        self.quit_button.clicked.connect(QApplication.quit)
        self.quit_button.setToolTip("Anwendung beenden.")
        self.quit_button.setFont(QFont('', FONT_SIZE))
        layout.addWidget(self.quit_button)

        self.setLayout(layout)

        if self.anweisungen_combo.count() > 0:
            self.anweisungen_combo.setCurrentIndex(0)

    def load_anweisungen(self):
        try:
            anweisungen = read_anweisungen(ANWEISUNGEN_FILE)
            if anweisungen:
                self.anweisungen_combo.addItems(anweisungen)
            else:
                QMessageBox.critical(self, 'Fehler', 'Keine Anweisungen gefunden. Bitte überprüfe die Datei anweisungen.txt.\nNo instructions found. Please check the file anweisungen.txt.')
        except Exception as e:
            QMessageBox.critical(self, 'Fehler', f'Fehler beim Lesen der Anweisungen: {str(e)}')

    def load_models(self):
        try:
            models = get_installed_models()
            if models:
                self.model_combo.addItems([f"Modell {k}: {v}" for k, v in models.items()])
            else:
                QMessageBox.critical(self, 'Fehler', 'Es sind keine Modelle installiert. Installiere bitte mindestens ein Modell.\nNo models are installed. Please install at least one model.')
        except Exception as e:
            QMessageBox.critical(self, 'Fehler', f'Fehler beim Laden der Modelle: {str(e)}')

    def generate_text(self):
        selected_anweisung = self.anweisungen_combo.currentText()
        try:
            selected_model = self.model_combo.currentText().split(': ')[1]
        except IndexError:
            QMessageBox.critical(self, 'Fehler', 'Ungültige Modellauswahl.')
            return
        user_input = self.begriffe_input.toPlainText().strip()

        if not user_input:
            QMessageBox.warning(self, 'Fehler', 'Die Eingabe darf nicht leer sein.\nThe input must not be empty')
            return

        try:
            generated_text = generate_ollama_prompt(selected_anweisung, user_input, selected_model)
            if not generated_text:
                QMessageBox.critical(self, 'Fehler', 'Fehler bei der Generierung des Textes!')
                return

            self.generated_text_edit.setPlainText(generated_text)

            dlg = PromptEditDialog(generated_text)
            if dlg.exec():
                edited_prompt = dlg.get_edited_prompt()
                self.generated_text_edit.setPlainText(edited_prompt)
                date = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                save_to_csv(str(PROMPTS_CSV), date, user_input, selected_model, edited_prompt)
                append_to_prompt_txt(edited_prompt, str(PROMPT_TXT))
                clean_csv(str(PROMPTS_CSV))
            else:
                QMessageBox.critical(self, 'Hinweis', 'Prompt wird nicht gespeichert!\nPrompt not saved!')

        except Exception as e:
            QMessageBox.critical(self, 'Fehler', f'Fehler bei der Generierung: {str(e)}')

    def copy_to_clipboard(self):
        generated_text = self.generated_text_edit.toPlainText()
        if generated_text:
            clipboard = QApplication.clipboard()
            clipboard.setText(generated_text)
            self.copy_to_clipboard_button.setStyleSheet("background-color: green")
            QTimer.singleShot(100, self.reset_button_color)
        else:
            QMessageBox.warning(self, 'Fehler', 'Es gibt keinen generierten Text, der in die Zwischenablage kopiert werden kann.\nThere is no generated text that can be copied to the clipboard.')

    def reset_button_color(self):
        self.copy_to_clipboard_button.setStyleSheet("")


# ===== Hauptprogramm =====
if __name__ == '__main__':
    app = QApplication(sys.argv)

    app.setFont(QFont("Arial", 16))
    app.setStyleSheet(
        "QWidget { font-size: 16pt; }"
        "QPushButton { font-size: 16pt; padding: 10px; }"
    )

    ex = App()
    ex.show()
    sys.exit(app.exec())
