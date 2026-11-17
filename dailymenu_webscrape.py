from codecs import xmlcharrefreplace_errors
'''
spusteni v terminalu:
python -m venv prostredi     
source prostredi/bin/activate
pip install -r requirements.txt
python flask_app.py
'''

import os
import subprocess
import requests
import logging
import re
from bs4 import BeautifulSoup
from datetime import date

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)

seznam_restauraci = {
    "technicka_menza": "https://agata.suz.cvut.cz/jidelnicky/index.php?clPodsystem=3&lang=cs",
    "jidlovice": "https://www.jidlovice.cz/telehouse/",
    "jidelna17": "https://www.jidelna17.cz/tydenni-menu",
    "restaurant_kulatak": "https://kulatak.cz/#menu-obsah",
    "cafe_prostoru": "https://streva.prostoru.cz/jidelnicekvlozeny.php",
    "studentska_menza": "https://agata.suz.cvut.cz/jidelnicky/index.php?clPodsystem=2&lang=cs",
    "utopolu": "http://www.utopolu.cz/menu",
#"U Petnika": "",
}

# OCR: Tesseract binary + Czech model stored in the project (./tessdata/ces.traineddata)
TESSDATA_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "tessdata")

def get_web(url):
    try:
        response = requests.get(url)
        page_html = response.text
        page = BeautifulSoup(page_html, features="html.parser") # veme html co se stahl a zparsuje ten STRING plnej html ho do actual python objektu
        return page
    except Exception as e:
        logger.error(f"Unexpected error: {e}")


def get_jidlovice_api():
    try:
        dnesni_datum = date.today().strftime('%Y-%m-%d')
        url = "https://jidlovice.cz/api/v1/branch/3/menu/" + dnesni_datum
        response = requests.get(url)
        jidlovice_dict = response.json()
        return jidlovice_dict
    except Exception as e:
        logger.error(f"Unexpected error: {e}")


def scrape_jidlovice(jidlovice_dict):
    try:
        menu = []
        for jedno_jidlo in jidlovice_dict["menu_items"]:
            nazev_jidla = jedno_jidlo["meal"]["name"] #nested dictionary - value může být cokoli - i další dictionary
            # výjimka: jídla ve sklenici/skle na domů ("0,33l sklenice", "0,66l sklo(2 porce)") nechceme
            if re.search(r"\d+(?:[.,]\d+)?\s*l\s*skl(?:enice|o)", nazev_jidla, re.IGNORECASE):
                continue
            popis_jidla = jedno_jidlo["meal"]["description"]
            cena_jidla = jedno_jidlo["meal"]["price"]
            dict = {"text_jidlo": nazev_jidla + (popis_jidla if popis_jidla is not None else ""), "text_cena": cena_jidla} #debug, jinak když chybí třeba popis nebo název tak to tady crashlo
            menu.append(dict)
        logging.debug(menu)
        return menu
    except Exception as e:
        logger.error(f"Unexpected error: {e}")

def scrape_kulatak(page):
    try:
        menu = []
        container = page.find(attrs={"class": "elementor-element-425aa18"})
        paragraphs = container.find_all('p', style=re.compile(r'text-align\s*:\s*center', re.IGNORECASE)) #regex protože každý den mají to html trochu jiný
        pomocna_prom = ""
        for jeden_paragraf in paragraphs:
            text_paragrafu = jeden_paragraf.get_text().strip().replace("\n", "") # .strip zbaví zbytečných mezer .replace nový řádek za prázdný string
            if text_paragrafu != "":
                if (text_paragrafu[0].isdigit() and text_paragrafu[1] == ")") or "Specialita týdne" in text_paragrafu: #jejich formátování denní nabídky číslo) nebo týdenní specialita
                    pomocna_prom += text_paragrafu
                    continue
                if pomocna_prom != "":
                    if ",-" in text_paragrafu:
                        if len(text_paragrafu) > 6:
                            dict = {"text_jidlo": pomocna_prom + " " + text_paragrafu[0:-5], "text_cena": text_paragrafu[-5:]} #oddělení ceny od popisu pomocí indexování a slicingu protože regex je ouvej
                            pass
                        else:
                            dict = {"text_jidlo": pomocna_prom, "text_cena": text_paragrafu}
                        pomocna_prom = ""
                        menu.append(dict)
                    else:
                        pomocna_prom += " " + text_paragrafu
#použít regexp protože najednou dali cenu do stejnýho paragrafu jako zbytek jídla
#specialita týdne která pomocna proměnná najít specialitu týdne a pak to co je za tím
        logging.debug(menu)
        return menu
    except Exception as e:
        logger.error(f"Unexpected error: {e}")

def scrape_jidelna17(page):
    try:
        container = page.find(attrs={"id": "pondeli"})
        row_jidel = container.find_all(attrs={"class": "food-menu__list-item-row"})
        menu = []
        for jidlo in row_jidel:
            element_jidlo = jidlo.find(attrs={"class": "food-menu__list-item-title"})
            if element_jidlo is None:
                continue
            text_jidlo = element_jidlo.get_text().strip()
            text_cena = jidlo.find(attrs={"class": "food-menu__list-item-price"}).get_text()
            dic = {"text_jidlo": text_jidlo, "text_cena": text_cena}
            menu.append(dic)
        logging.debug(menu)
        return menu
    except Exception as e:
        logger.error(f"Unexpected error: {e}")

def scrape_technicka(page):
    try:
        menu = []
        containers = page.select("div.col.d-flex.flex-column.h-100")
        for container in containers:
            text_jidlo = container.find(attrs={"class": "card-title mb-1"}).get_text()
            text_cena = container.find(attrs={"class": "badge cena-badge me-2"}).get_text()
            dic = {"text_jidlo": text_jidlo, "text_cena": text_cena}
            menu.append(dic)
        logging.debug(menu)
        #zkontroluj že menu není prázdný, pokud ano použij týdenní menu
        #  raise NotImplementedError("jeste to nemam hotovy")
        if len(menu) == 0: ## if not menu
            pass
        return menu
    except Exception as e:
        logger.error(f"Unexpected error: {e}")

def scrape_studentska(page):
    try:
        menu = []
        containers = page.select("div.col.d-flex.flex-column.h-100")
        for container in containers:
            text_jidlo = container.find(attrs={"class": "card-title mb-1"}).get_text()
            text_cena = container.find(attrs={"class": "badge cena-badge me-2"}).get_text()
            dic = {"text_jidlo": text_jidlo, "text_cena": text_cena}
            menu.append(dic)
        logging.debug(menu)
        if len(menu) == 0:
            pass
        return menu
    except Exception as e:
        logger.error(f"Unexpected error: {e}")


def scrape_prostoru(page):
    dnesni_datum = date.today().strftime('%d.%-m.')
    try:
        menu = []
        container = page.find("table")
        table_rows = container.find_all("tr")
        for table_row in table_rows:
            elements_in_row = table_row.find_all("td")
            if len(elements_in_row) == 0:
                continue
            if dnesni_datum in elements_in_row[0].get_text():

                for radek in elements_in_row[1].contents:
                    if str(radek) == "<br/>":
                        continue
                    else:
                        text_jidlo = radek.get_text()
                        if "Polévka" in text_jidlo:  #hardcoded cena jídla protože je mají pro všechny stejné
                                text_cena = "60"
                        else:
                                text_cena = "165"
                        dic = {"text_jidlo": text_jidlo, "text_cena": text_cena}
                        menu.append(dic)
        logging.debug(menu)
        return menu
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        raise e

def ocr_image(image_bytes):
    """Pošle obrázek do Tesseractu (přes stdin) a vrátí rozpoznaný text."""
    result = subprocess.run(
        ["tesseract", "stdin", "stdout", "-l", "ces", "--psm", "6"],
        input=image_bytes,
        capture_output=True,
        env={**os.environ, "TESSDATA_PREFIX": TESSDATA_DIR},
        timeout=60,
        check=True,
    )
    return result.stdout.decode("utf-8")


# cena na konci řádku: "59,-", "289,- ©", ale OCR občas ztratí pomlčku ("275,")
CENA_NA_KONCI = re.compile(r"(\d{2,3}),\s*-?[^\w]*$")
# čísla alergenů těsně před cenou: "1,3,7,9", "1379."
ALERGENY_NA_KONCI = re.compile(r"\s+\d[\d,.]*\s*$")


def parse_utopolu_text(text):
    """Z OCR textu vyrobí seznam {"text_jidlo", "text_cena"}."""
    menu = []
    buffer = []
    v_menu = False  # ignorujeme vše před první sekcí (nadpis, datum, OCR šum)
    for radek in text.splitlines():
        radek = radek.strip()
        if not radek:
            continue
        if radek.startswith("Ve "):
            break  # "Ve středu se můžete těšit na:" = upoutávka na zítřek, ne dnešní menu
        if radek.endswith(":"):
            v_menu = True
            buffer = []
            continue
        if not v_menu:
            continue
        buffer.append(radek)
        cena = CENA_NA_KONCI.search(radek)
        if cena:
            text_jidlo = " ".join(buffer)
            text_jidlo = CENA_NA_KONCI.sub("", text_jidlo).rstrip()
            text_jidlo = ALERGENY_NA_KONCI.sub("", text_jidlo)
            text_jidlo = " ".join(text_jidlo.replace("|", "").split())
            menu.append({"text_jidlo": text_jidlo, "text_cena": cena.group(1) + ",-"})
            buffer = []
    return menu


def scrape_utopolu(page):
    """U Topolů dává denní menu jako obrázek (JPG), proto OCR."""
    try:
        img = page.find("img", src=re.compile(r"/daily-menus/"))
        if img is None:
            logger.warning("U Topolů: obrázek s menu nenalezen")
            return None
        img_url = img["src"]
        # v názvu souboru je datum (…-2026-11-17-denni-menu.jpg) - nechceme zobrazit včerejšek
        if date.today().strftime("%Y-%m-%d") not in img_url:
            logger.warning(f"U Topolů: menu není z dneška ({img_url})")
            return None
        image_bytes = requests.get(img_url, timeout=30).content
        menu = parse_utopolu_text(ocr_image(image_bytes))
        logging.debug(menu)
        return menu
    except Exception as e:
        logger.error(f"Unexpected error: {e}")


def restaurants_all():
    vsechny_restaurants = {}
    for NAZEV_RESTAURACE, url in seznam_restauraci.items():
        if NAZEV_RESTAURACE == "technicka_menza":
            scraped_technicka_menza = scrape_technicka(get_web(url))
            vsechny_restaurants["Technická menza"] = scraped_technicka_menza
        elif NAZEV_RESTAURACE == "studentska_menza":
            scraped_technicka_menza = scrape_technicka(get_web(url))
            vsechny_restaurants["Studentská menza"] = scraped_technicka_menza
        elif NAZEV_RESTAURACE == "jidlovice":
            scraped_jidlovice = scrape_jidlovice(get_jidlovice_api())
            vsechny_restaurants["Jídlovice Telehouse"] = scraped_jidlovice
        elif NAZEV_RESTAURACE == "restaurant_kulatak":
            scraped_kulatak = scrape_kulatak(get_web(url))
            vsechny_restaurants["Kulaťák"] = scraped_kulatak
        elif NAZEV_RESTAURACE == "jidelna17":
            scraped_jidelna17 = scrape_jidelna17(get_web(url))
            vsechny_restaurants["Jídelna 17"] = scraped_jidelna17
        elif NAZEV_RESTAURACE == "cafe_prostoru":
            scraped_cafe_prostoru = scrape_prostoru(get_web(url))
            vsechny_restaurants["Café Prostoru"] = scraped_cafe_prostoru
        elif NAZEV_RESTAURACE == "utopolu":
            scraped_utopolu = scrape_utopolu(get_web(url))
            vsechny_restaurants["U Topolů"] = scraped_utopolu
    return vsechny_restaurants

if __name__ == "__main__":
    restaurants_all()
