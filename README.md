<div align=center><h1>Promptgenerator 2.5 with Ollama</h1></div>
<p align="center">
  <img src="bilder/bild.png" />
  <img src="bilder/prompt1.png" />
</p>

<p align="center">
  <img src="bilder/prompt2_app.png" />
  <img src="bilder/prompt2.png" />
</p>

## This program now has a GUI with a button for the clipboard.

Install Ollama
<http://ollama.com>

My Favorite LLM for this program<br>
llama3.2:3b-instruct-q8_0

```sh
ollama pull llama3.2:3b-instruct-q8_0
```

Install Git
<https://git-scm.com/downloads>

Install Python
<https://www.python.org/downloads/>

<h2>Clone Repository</h2>

```sh
git clone https://github.com/MarkusR1805/promptgenerator.git
```

<img src="https://image.civitai.com/xG1nkqKTMzGDvpLrqFT7WA/c5769d49-f39a-4b84-9d27-b20ee9e625ba/original=true,quality=90/2024-10-26-163521.jpeg" alt="swirl, smoke, surreal, woman, portrait" title="Promptgenerator"/>

<h2>Create python venv</h2>

```sh
git clone https://github.com/MarkusR1805/promptgenerator.git
python -m venv promptgenerator
source promptgenerator/bin/activate
cd promptgenerator
```

<h1>Attention, very important!</h1>
If the program does not start or an error message appears, be sure to execute the requirements.txt.

```sh
pip install -r requirements.txt
```

<h2>Programm start</h2>

```sh
python main.py
```
