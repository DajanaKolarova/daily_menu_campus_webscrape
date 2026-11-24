# Denní menu webscrape

Jednoduchá webová aplikace ve Flasku, která stáhne denní menu z několika restaurací z okolí kampusu 
a zobrazí je na jedné přehledné stránce.

## Použité technologie
- **Python 3**
- **Flask** – web server a routování (`/`)
- **requests** – HTTP požadavky na weby restaurací
- **BeautifulSoup (bs4)** – parsování HTML a scraping
- **Tesseract OCR** – rozpoznání textu z obrázku s menu (U Topolů, menu je každý den JPG)
- **Playwright (headless Chromium)** – stránky, které si menu doskládají JavaScriptem (Vera Kitchen)
- **Leaflet + OpenStreetMap** – mapa restaurací dole na stránce (souřadnice jsou v `lokace.py`, mapa se načítá z internetu)
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

### Playwright (prohlížeč pro Vera Kitchen)
Po `pip install` je potřeba jednorázově stáhnout prohlížeč (~100 MB):
```
playwright install chromium
```
Bez něj aplikace funguje dál, jen u Vera Kitchen se zobrazí hláška, že menu není.

### Docker (volitelně)
V image je všechno hotové (Python, závislosti, Tesseract s češtinou, Chromium pro Playwright), takže na počítači stačí jen Docker:
```
docker build -t dame-obed .
docker run --rm -p 9999:9999 dame-obed
```
Pak otevři http://localhost:9999. Načtení stránky trvá desítky sekund (scrapery, OCR, Chromium).
V kontejneru běží `gunicorn` a časová zóna je nastavená na `Europe/Prague`.

### spuštění flask aplikace 
```
python flask_app.py
```