from datetime import datetime
from flask import Flask, render_template
from dailymenu_webscrape import restaurants_all
from lokace import LOKACE
app = Flask(__name__)

# --- hlášky, když menu chybí (tady je můžeš přepisovat) ---
HLASKA_BRZO = "Zatím je asi na denní menu brzy, zkus to za chvíli ;)"
HLASKA_POZDE = "Už je vše asi vyjedený"
HLASKA_CHYBA = "Chybička se vloudila zkus ofiko web…"

HODINA_OD = 11   # před 11:00 je brzy
HODINA_DO = 15   # od 15:00 je pozdě


def failure_message():
    """Vybere hlášku pro restauraci, jejíž menu se nepodařilo získat (menu is None).
    Šablona ji volá jen v tom případě - když menu existuje, hláška se vůbec nezobrazí.
    """
    hodina = datetime.now().hour
    if hodina < HODINA_OD:
        return HLASKA_BRZO
    if hodina >= HODINA_DO:
        return HLASKA_POZDE
    return HLASKA_CHYBA


@app.route('/')
def index():
    restaurants_result = restaurants_all()
    return render_template("index.html", restaurants=restaurants_result, failure_message=failure_message, lokace=LOKACE)

if __name__ == "__main__":
    app.run(debug=True, port=9999)
