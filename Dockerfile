# Dockerfile = recept, podle kterého se postaví image (obraz) s celou appkou.
# Postavení:  docker build -t dame-obed .
# Spuštění:   docker run --rm -p 9999:9999 dame-obed      (pak http://localhost:9999)

FROM python:3.13-slim

# - PYTHONUNBUFFERED: logy se hned vypisují (vidíš je v `docker logs`)
# - TZ: kontejner by jinak běžel v UTC a appka by špatně poznala "dnešek" a denní dobu
#   (date.today() a hláška "brzy/pozdě" se řídí časem v kontejneru)
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    TZ=Europe/Prague

# tesseract-ocr = OCR pro U Topolů (český jazykový model je v ./tessdata), tzdata = časová pásma
RUN apt-get update \
    && apt-get install -y --no-install-recommends tesseract-ocr tzdata \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Nejdřív jen requirements.txt: dokud se nezmění, Docker použije uloženou vrstvu a nestahuje všechno znovu
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Chromium pro Playwright (Vera Kitchen) + systémové knihovny, které potřebuje
RUN playwright install --with-deps chromium \
    && rm -rf /var/lib/apt/lists/*

# Až nakonec kód appky - ten se mění nejčastěji, takže se přestavuje jen tahle (rychlá) vrstva
COPY . .

EXPOSE 9999

# gunicorn místo vývojového serveru Flasku (ten je jen na zkoušení).
# --timeout 120: načtení stránky trvá desítky sekund (scrapery + OCR + Chromium), výchozích 30 s by nestačilo
CMD ["gunicorn", "--bind", "0.0.0.0:9999", "--workers", "2", "--timeout", "120", "flask_app:app"]
