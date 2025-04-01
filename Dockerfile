# Usa un'immagine base di Python
FROM python:3.9-slim

# Imposta la directory di lavoro
WORKDIR /app

# Copia i file del progetto nella directory di lavoro
COPY . /app

# Installa le dipendenze
RUN apt-get update && apt-get install -y \
    chromium \
    && pip install --no-cache-dir -r requirements.txt

# Imposta le variabili di ambiente
ENV PYTHONUNBUFFERED 1
ENV DISPLAY=:99

# Esegui il bot
CMD ["python", "Spy_price_bot.py"]
