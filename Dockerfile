# Usa l'immagine ufficiale di Python come base
FROM python:3.9-slim

# Imposta la working directory nel container
WORKDIR /app

# Installa le dipendenze di sistema necessarie per Chromium e ChromeDriver
RUN apt-get update && \
    apt-get install -y \
    chromium=134.0.6998.117-1 \
    libnss3 \
    libgdk-pixbuf2.0-0 \
    libatk-bridge2.0-0 \
    libatk1.0-0 \
    libcups2 \
    libxss1 \
    libappindicator3-1 \
    libasound2 \
    libnspr4 \
    libx11-xcb1 \
    libgbm1 \
    && apt-get clean

# Installa pip, aggiorna le dipendenze e installa i pacchetti Python necessari
RUN pip install --upgrade pip
RUN pip install selenium webdriver-manager aiogram python-dotenv requests

# Copia il codice del progetto nella working directory del container
COPY . /app

# Imposta variabili d'ambiente per Chromium
ENV CHROME_BIN=/usr/bin/chromium

# Comando per eseguire il bot
CMD ["python", "spy_price_bot.py"]
