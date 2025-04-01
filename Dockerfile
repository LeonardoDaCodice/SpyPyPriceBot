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
    unzip \
    && rm -rf /var/lib/apt/lists/*

# Imposta variabili per il binary di Chromium
ENV CHROMIUM_PATH=/usr/bin/chromium
ENV PATH="/usr/local/bin:$PATH"

# Scarica e installa ChromeDriver per la versione corretta di Chromium
RUN CHROMIUM_VERSION=$(chromium --version | awk '{print $2}' | cut -d'.' -f1-3) && \
    echo "Chromium Version: $CHROMIUM_VERSION" && \
    wget -q "https://chromedriver.storage.googleapis.com/${CHROMIUM_VERSION}/chromedriver_linux64.zip" -O /chromedriver.zip && \
    unzip /chromedriver.zip -d /usr/local/bin && \
    chmod +x /usr/local/bin/chromedriver && \
    rm /chromedriver.zip

# Installa le dipendenze Python
COPY requirements.txt /app/requirements.txt
RUN pip install --no-cache-dir -r /app/requirements.txt

# Copia il codice dell'applicazione
COPY . /app

WORKDIR /app

# Comando di avvio dell'applicazione
CMD ["python", "spy_price_bot.py"]
