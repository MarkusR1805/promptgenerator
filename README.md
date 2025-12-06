<div align=center><h1>Promptgenerator 2.5 with Ollama</h1></div>
<p align="center">
  <img src="bilder/prinz5.jpg" />
</p>
## This program now has a GUI with a button for the clipboard.

Install Ollama
<http://ollama.com>

My Favorite LLM for this program<br>
llama3.2:3b

```sh
ollama pull llama3.2:3b
```

<p align="center">
  <img src="bilder/bild2.png" />
</p>

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
python -m venv promptgenerator
source promptgenerator/bin/activate
cd promptgenerator
```

<h1>Attention, very important!</h1>
If the program does not start or an error message appears, be sure to execute the requirements.txt.

```sh
pip install -r requirements.txt
```

> # Troubleshooting

> If an installation does not work for whatever reason, but you have installed Python, you have the following option:
>
> - start your terminal and type the following: cd
> - install all the libraries listed below by hand
> - pip install anyio==4.6.2.post1
> - pip install certifi==2024.8.30
> - etc.

These Python libraries should be installed!

- anyio==4.6.2.post1
- certifi==2024.8.30
- h11==0.14.0
- httpcore==1.0.6
- httpx==0.27.2
- idna==3.10
- ollama==0.4.3
- sniffio==1.3.1
- PyQt6==6.7.1
- PyQt6-Qt6==6.7.3
- PyQt6_sip==13.8.0
- sniffio==1.3.1

<h2>Programm start</h2>

```sh
python main.py
```

![Promptgenerator](https://image.civitai.com/xG1nkqKTMzGDvpLrqFT7WA/26f2122f-6738-45e1-bcf9-0e62f281622c/original=true,quality=90/36686347.jpeg)
