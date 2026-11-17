# Denní menu webscrape

Jednoduchá webová aplikace ve Flasku, která stáhne denní menu z několika restaurací z okolí kampusu 
a zobrazí je na jedné přehledné stránce.

## Použité technologie
- **Python 3**
- **Flask** – web server a routování (`/`)
- **requests** – HTTP požadavky na weby restaurací
- **BeautifulSoup (bs4)** – parsování HTML a scraping
- **Tesseract OCR** – rozpoznání textu z obrázku s menu (U Topolů, menu je každý den JPG)
- **logging** – logování chyb a debug informací
- **Jinja2** – templating (součást Flasku), rendrování `templates/index.html`

## spuštění
### Virtualni prostředí
```
python -m venv prostredi
source prostredi/bin/activate
```

### nainstalování závislostí: 
```
pip install -r requirements.txt
```

### Tesseract (OCR)
Program `tesseract` musí být v PATH (není to Python balíček):
```
brew install tesseract          # macOS
sudo apt install tesseract-ocr  # Debian/Ubuntu
```
Český jazykový model je ve složce `tessdata/ces.traineddata` (aplikace na ni ukazuje sama přes `TESSDATA_PREFIX`).
Pokud chybí, stáhni ho z https://github.com/tesseract-ocr/tessdata_fast.

### spuštění flask aplikace 
```
python flask_app.py
```