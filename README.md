# 🕵️ SpyPyPriceBot

SpyPyPriceBot è un bot Telegram scritto in Python che permette agli utenti di **monitorare i prezzi dei prodotti** su **AliExpress** e **Amazon**. Il bot avvisa automaticamente l'utente quando:

- 💰 Il prezzo di un prodotto varia (in modalità monitoraggio generale)
- 🎯 Il prezzo scende sotto un prezzo target definito (modalità con target)

![Anteprima del bot](images/Immagine_bot.jpg)

---

##  Funzionalità principali

- Tracciamento dei prezzi da link di Amazon o AliExpress
- Due modalità di monitoraggio:
  - Monitoraggio di tutte le variazioni di prezzo
  - Monitoraggio con prezzo target
- Notifiche Telegram automatiche sugli aggiornamenti dei prezzi
- Gestione dei link monitorati:
  - Visualizzazione dei prodotti
  - Navigazione tra i prodotti
  - Eliminazione singola
- Database locale (`prices.db`) per memorizzare i link monitorati
- Periodico controllo dei prezzi ogni 10 minuti
- Utilizzo di `Selenium` per recuperare i prezzi in modo dinamico

---

##  Requisiti

- Python 3.10+
- Token Telegram Bot (da inserire nel file `.env`)

---

##  Installazione

1. **Clona il repository**:

   ```bash
   git clone https://github.com/tuo-utente/SpyPyPriceBot.git
   cd SpyPyPriceBot
   ```

2. **Crea e attiva un ambiente virtuale**:

   ```bash
   python -m venv .venv
   .venv\Scripts\activate       # Su Windows
   source .venv/bin/activate   # Su Linux/macOS
   ```

3. **Installa le dipendenze**:

   ```bash
   pip install -r requirements.txt
   ```

4. **Crea un file `.env`** con il tuo token del bot:

   ```env
   BOT_TOKEN=il_tuo_token
   ```

5. **Avvia il bot**:

   ```bash
   python spy_price_bot.py
   ```

---

##  Esempio d’uso

- Avvia il bot su Telegram con il comando `/start`
- Clicca su **"Monitora un prodotto"**
- Invia un link Amazon o AliExpress
- Scegli una modalità:
  - 📉 Per ricevere tutte le variazioni di prezzo
  - 🎯 Per inserire un prezzo target

> ⚠️ Se il prezzo attuale è già inferiore al target inserito, il bot ti inviterà a inserirne uno più basso.

---

## 📂 Struttura del progetto

```
SpyPyPriceBot/
├── spy_price_bot.py         # Codice principale del bot
├── .env                     # File che contiene il token del bot, che dovrai creare manualmente (non incluso nel repository perché non va pushato)
├── .gitignore               # File di configurazione Git
├── requirements.txt         # Dipendenze da installare
├── README.md                # Questo file
└── prices.db                # Database SQLite generato automaticamente
```


---

##  Autore

**LeonardoDaCodice** Progetto personale per apprendere lo sviluppo Python, l'utilizzo di bot Telegram e tecniche di web scraping.

---

##  Licenza

Questo progetto è open source e distribuito sotto la licenza **MIT**.Sentiti libero di usarlo, modificarlo e contribuire!

---

##  Contatti

Hai domande o suggerimenti?Apri una [issue](https://github.com/tuo-utente/SpyPyPriceBot/issues) oppure scrivi direttamente nel repository!

