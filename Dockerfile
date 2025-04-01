# Usa l'immagine ufficiale di Python come base
FROM python:3.9-slim

# Imposta la working directory nel container
WORKDIR /app

# Installa le dipendenze di sistema necessarie per Chromium
RUN apt-get update && \
    apt-get install -y \
    chromium \
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

# Crea e attiva un ambiente virtuale
RUN python -m venv /venv
ENV PATH="/venv/bin:$PATH"

# Installa pip e le dipendenze Python necessarie nell'ambiente virtuale
RUN pip install --upgrade pip
RUN pip install selenium webdriver-manager aiogram python-dotenv requests

# Copia il codice del progetto nella working directory del container
COPY . /app

# Imposta variabili d'ambiente per Chromium
ENV CHROME_BIN=/usr/bin/chromium

# Comando per eseguire il bot
CMD ["python", "spy_price_bot.py"]
