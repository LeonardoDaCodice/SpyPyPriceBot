FROM python:3.11-slim

# Installa le dipendenze necessarie per Chromium e jq
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
    jq \
    && rm -rf /var/lib/apt/lists/*

# Imposta variabili per il binary di Chromium
ENV CHROMIUM_PATH=/usr/bin/chromium
ENV PATH="/usr/local/bin:$PATH"

# Scarica la versione di ChromeDriver compatibile con Chromium
RUN CHROMIUM_VERSION=$(chromium --version | awk '{print $2}') && \
    echo "Chromium Version: $CHROMIUM_VERSION" && \
    CHROMEDRIVER_VERSION=$(wget -qO- "https://googlechromelabs.github.io/chrome-for-testing/latest-patch-versions-per-build.json" | \
    jq -r ".builds[\"${CHROMIUM_VERSION%%.*}\"].version") && \
    echo "Downloading ChromeDriver version: $CHROMEDRIVER_VERSION" && \
    wget -q "https://storage.googleapis.com/chrome-for-testing-public/${CHROMEDRIVER_VERSION}/linux64/chromedriver-linux64.zip" -O /chromedriver.zip && \
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
