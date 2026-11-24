from codecs import xmlcharrefreplace_errors
'''
spusteni v terminalu:
python -m venv prostredi     
source prostredi/bin/activate
pip install -r requirements.txt
python flask_app.py
'''

import os
import json
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
    "vera_kitchen": "https://www.verakitchen.cz/menu/",
    "u_petnika": "https://upetnika.cz/",
    "na_kotlarce": "https://nakotlarce.cz/menu/section:denni-menu/denni-menu",
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


def get_web_rendered(url, hotovo_js, timeout_ms=30000):
    """Stáhne stránku, jejíž obsah se doskládává JavaScriptem (requests by viděl jen prázdnou kostru).
    Otevře ji v headless Chromiu (Playwright) a počká, až platí JS podmínka hotovo_js."""
    try:
        from playwright.sync_api import sync_playwright  # import tady, ať appka běží i bez Playwrightu
        with sync_playwright() as p:
            browser = p.chromium.launch()
            try:
                page = browser.new_page()
                page.goto(url, wait_until="domcontentloaded", timeout=timeout_ms)
                page.wait_for_function(hotovo_js, timeout=timeout_ms)
                return BeautifulSoup(page.content(), features="html.parser")
            finally:
                browser.close()
    except Exception as e:
        logger.error(f"Unexpected error (rendered page {url}): {e}")


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
        denni_menu = []
        stala_nabidka = []  # jídla, co mají pořád (API je značí meal["permanent"]) - zobrazí se až pod denním menu
        for jedno_jidlo in jidlovice_dict["menu_items"]:
            nazev_jidla = jedno_jidlo["meal"]["name"] #nested dictionary - value může být cokoli - i další dictionary
            # výjimka: jídla ve sklenici/skle na domů ("0,33l sklenice", "0,66l sklo(2 porce)") nechceme
            if re.search(r"\d+(?:[.,]\d+)?\s*l\s*skl(?:enice|o)", nazev_jidla, re.IGNORECASE):
                continue
            popis_jidla = jedno_jidlo["meal"]["description"]
            cena_jidla = jedno_jidlo["meal"]["price"]
            dict = {"text_jidlo": nazev_jidla + (popis_jidla if popis_jidla is not None else ""), "text_cena": cena_jidla} #debug, jinak když chybí třeba popis nebo název tak to tady crashlo
            if jedno_jidlo["meal"].get("permanent"):
                dict["stala"] = True
                stala_nabidka.append(dict)
            else:
                denni_menu.append(dict)
        menu = denni_menu + stala_nabidka
        logging.debug(menu)
        return menu
    except Exception as e:
        logger.error(f"Unexpected error: {e}")

def scrape_kulatak(page):
    """Kulaťák: sekce #denni-menu, každé jídlo je <div class="menu-item"> (název, cena, popis)."""
    try:
        sekce = page.find("section", id="denni-menu")
        # v nadpisu je datum, pro které menu platí ("Aktuální polední lístek pro 25.11.2026")
        datum_text = sekce.find("h2").get_text(" ", strip=True)
        datum = re.search(r"(\d{1,2})\.\s*(\d{1,2})\.\s*(\d{4})", datum_text)
        dnes = date.today()
        if datum is None or (int(datum.group(1)), int(datum.group(2)), int(datum.group(3))) != (dnes.day, dnes.month, dnes.year):
            logger.warning(f"Kulaťák: menu není z dneška ({datum_text})")
            return None

        denni_menu = []
        stala_nabidka = []  # jídla, co mají každý den - zobrazí se až pod denním menu
        for blok in sekce.find_all("div", class_="menu-block"):
            je_stala = "menu-block-stala" in blok.get("class", [])
            for jidlo in blok.find_all("div", class_="menu-item"):
                nazev = jidlo.find(class_="menu-item-name").get_text(" ", strip=True)  # "1) Ledvinky"
                cena = jidlo.find(class_="menu-item-price").get_text(strip=True)  # "178,-"
                popis = jidlo.find(class_="menu-item-desc")  # u polévky není
                text_jidlo = nazev + (" – " + popis.get_text(" ", strip=True) if popis else "")
                if je_stala:
                    stala_nabidka.append({"text_jidlo": text_jidlo, "text_cena": cena, "stala": True})
                else:
                    denni_menu.append({"text_jidlo": text_jidlo, "text_cena": cena})
        menu = denni_menu + stala_nabidka
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


def scrape_upetnika(page):
    """U Pětníka: denní menu je v div.ural-type-daily, nadpis obsahuje datum ("Denní nabídka 24.11.2026"),
    jídla jsou <li class="ural-item"> (název + cena)."""
    try:
        kontejner = page.select_one("div.ural-menu-container.ural-type-daily")
        nadpis = kontejner.select_one("h3.ural-main-title").get_text(" ", strip=True)
        datum = re.search(r"(\d{1,2})\.\s*(\d{1,2})\.\s*(\d{4})", nadpis)
        dnes = date.today()
        if datum is None or tuple(int(c) for c in datum.groups()) != (dnes.day, dnes.month, dnes.year):
            logger.warning(f"U Pětníka: menu není z dneška ({nadpis})")
            return None
        menu = []
        for polozka in kontejner.select("li.ural-item"):
            text_jidlo = polozka.select_one(".ural-name").get_text(" ", strip=True)
            cena = polozka.select_one(".ural-price").get_text(strip=True)
            menu.append({"text_jidlo": text_jidlo, "text_cena": cena + " Kč"})
        logging.debug(menu)
        return menu
    except Exception as e:
        logger.error(f"Unexpected error: {e}")


def scrape_nakotlarce(page):
    """Na Kotlářce (ChoiceQR): menu je v JSON-LD (schema.org Restaurant -> hasMenu) přímo v HTML.
    Stránka u menu neuvádí datum, takže se nedá ověřit, že je z dneška."""
    try:
        menu = []
        for skript in page.find_all("script", type="application/ld+json"):
            data = json.loads(skript.string)
            if not (isinstance(data, dict) and data.get("@type") == "Restaurant" and "hasMenu" in data):
                continue
            for sekce in data["hasMenu"]["hasMenuSection"]:
                for polozka in sekce["hasMenuItem"]:
                    text_jidlo = " ".join(polozka["name"].split())  # "0,3l\tPolévka" -> "0,3l Polévka"
                    text_jidlo = re.sub(r"\s*\([\d,\s]+\)$", "", text_jidlo)  # čísla alergenů na konci "(1,3,7)"
                    menu.append({"text_jidlo": text_jidlo, "text_cena": polozka["offers"]["price"] + " Kč"})
        if not menu:
            return None
        logging.debug(menu)
        return menu
    except Exception as e:
        logger.error(f"Unexpected error: {e}")


# Vera Kitchen skládá menu JavaScriptem (do té doby je na stránce "Načítám menu…"),
# hotovo = zmizel placeholder a objevila se jídla nebo hláška "Dnes máme zavřeno"
VERA_HOTOVO_JS = """() => !document.body.innerText.includes('Načítám menu')
    && (document.querySelector('section.vk-card .vk-row') !== null
        || document.body.innerText.includes('Dnes máme zavřeno'))"""


def scrape_vera(page):
    """Vera Kitchen (Jídelna BLOX): při načtení je zobrazené dnešní menu - karty Polévky a Hlavní jídla.
    Stálá nabídka ("každý den") se přidá až za denní menu. Cena = běžná (ne cena pro členy VERA klubu)."""
    try:
        dnes = date.today()
        denni_menu = []
        stala_nabidka = []
        for karta in page.select("section.vk-card"):
            je_stala = karta.select_one(".vk-h span").get_text(strip=True).startswith("Stálá")
            if not je_stala:
                stitek = karta.select_one(".vk-dl")  # "Úterý 24. 11."
                datum = re.search(r"(\d{1,2})\.\s*(\d{1,2})\.", stitek.get_text()) if stitek else None
                if datum is None or (int(datum.group(1)), int(datum.group(2))) != (dnes.day, dnes.month):
                    logger.warning(f"Vera Kitchen: menu není z dneška ({stitek.get_text(strip=True) if stitek else '?'})")
                    return None
            for radek in karta.select(".vk-row"):
                text_jidlo = radek.select_one(".vk-n").get_text(" ", strip=True)
                if "so" in radek.get("class", []):
                    text_jidlo += " (vyprodáno)"
                cena = radek.select_one(".vk-pb")  # "běžná 217 Kč"
                text_cena = cena.get_text(strip=True).replace("běžná", "").strip() if cena else radek.select_one(".vk-pv").get_text(strip=True)
                if je_stala:
                    stala_nabidka.append({"text_jidlo": text_jidlo, "text_cena": text_cena, "stala": True})
                else:
                    denni_menu.append({"text_jidlo": text_jidlo, "text_cena": text_cena})
        if not denni_menu:
            return None  # "Dnes máme zavřeno" (víkend, svátek) - stálá nabídka sama o sobě není denní menu
        menu = denni_menu + stala_nabidka
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
        elif NAZEV_RESTAURACE == "vera_kitchen":
            scraped_vera = scrape_vera(get_web_rendered(url, VERA_HOTOVO_JS))
            vsechny_restaurants["Vera Kitchen"] = scraped_vera
        elif NAZEV_RESTAURACE == "u_petnika":
            scraped_petnik = scrape_upetnika(get_web(url))
            vsechny_restaurants["U Pětníka"] = scraped_petnik
        elif NAZEV_RESTAURACE == "na_kotlarce":
            scraped_kotlarka = scrape_nakotlarce(get_web(url))
            vsechny_restaurants["Na Kotlářce"] = scraped_kotlarka
    return vsechny_restaurants

if __name__ == "__main__":
    restaurants_all()
