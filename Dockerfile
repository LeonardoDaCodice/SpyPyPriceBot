FROM python:3.11-slim

# Installa le dipendenze necessarie per Chromium
RUN apt-get update && apt-get install -y \
    wget \
    ca-certificates \
    fonts-liberation \
    libappindicator3-1 \
    libnss3 \
    lsb-release \
    xdg-utils \
    chromium \
    && rm -rf /var/lib/apt/lists/*

# Imposta variabili per il binary di Chromium
ENV CHROMIUM_PATH=/usr/bin/chromium

# Installa le dipendenze Python
COPY requirements.txt /app/requirements.txt
RUN pip install --no-cache-dir -r /app/requirements.txt

# Copia il codice dell'applicazione
COPY . /app

WORKDIR /app

# Comando di avvio dell'applicazione
CMD ["python", "spy_price_bot.py"]
