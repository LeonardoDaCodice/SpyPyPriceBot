# Usa un'immagine base di Python
FROM python:3.9-slim

# Imposta la directory di lavoro
WORKDIR /app

# Copia i file del progetto nella directory di lavoro
COPY . /app

RUN apt-get update && apt-get install -y wget unzip && \
    wget -O /tmp/chromedriver.zip https://storage.googleapis.com/chrome-for-testing-public/134.0.6998.117/linux64/chromedriver-linux64.zip && \
    unzip /tmp/chromedriver.zip -d /usr/local/bin/ && \
    rm /tmp/chromedriver.zip

# Imposta le variabili di ambiente
ENV PYTHONUNBUFFERED 1
ENV DISPLAY=:99

# Esegui il bot
CMD ["python", "spy_price_bot.py"]
