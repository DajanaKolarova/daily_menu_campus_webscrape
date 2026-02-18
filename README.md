# Denní menu webscrape

Jednoduchá webová aplikace ve Flasku, která stáhne denní menu z několika restaurací z okolí kampusu 
a zobrazí je na jedné přehledné stránce.

## Použité technologie
- **Python 3**
- **Flask** – web server a routování (`/`)
- **requests** – HTTP požadavky na weby restaurací
- **BeautifulSoup (bs4)** – parsování HTML a scraping
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

### spuštění flask aplikace 
```
python flask_app.py
```