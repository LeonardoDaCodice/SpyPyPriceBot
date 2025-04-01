import asyncio
import time
import os
import logging
import sqlite3
from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager
from dotenv import load_dotenv

# Carica le variabili d'ambiente
load_dotenv()
TOKEN = os.getenv('BOT_TOKEN')

# Inizializza il bot e il dispatcher
bot = Bot(token=TOKEN)
dp = Dispatcher()

# Variabile globale per tenere traccia degli indici degli utenti
user_links_index = {}

# Configurazione Selenium con Chrome headless
chrome_options = Options()
chrome_options.add_argument("--headless")
chrome_options.add_argument("--disable-gpu")
chrome_options.add_argument("--no-sandbox")
chrome_options.add_argument("--disable-dev-shm-usage")

# Inizializza il WebDriver
service = Service(ChromeDriverManager().install())
driver = webdriver.Chrome(service=service, options=chrome_options)

# Database SQLite
conn = sqlite3.connect("prices.db", check_same_thread=False)
cursor = conn.cursor()

# Creazione tabelle
cursor.execute("""
    CREATE TABLE IF NOT EXISTS products (
        id INTEGER PRIMARY KEY, 
        chat_id INTEGER, 
        url TEXT, 
        price FLOAT, 
        last_checked TIMESTAMP
    )
""")

cursor.execute("""
    CREATE TABLE IF NOT EXISTS users (
        chat_id INTEGER PRIMARY KEY
    )
""")
conn.commit()

async def show_links_with_navigation(chat_id, callback_query=None):
    cursor.execute("SELECT url FROM products WHERE chat_id = ?", (chat_id,))
    urls = cursor.fetchall()

    if not urls:
        if callback_query:
            await callback_query.answer()
        await bot.send_message(chat_id, "❌ Non stai monitorando alcun link.")
        return

    # Recupera l'indice corrente dell'utente (se presente)
    index = user_links_index.get(chat_id, 0)
    total = len(urls)  # Numero totale di prodotti monitorati

    # Mostra solo il link corrente
    current_url = urls[index][0]
    message_text = f"🔗 Link monitorato {index + 1} di {total}:\n{current_url}"

    # Crea la tastiera inline con pulsanti per la navigazione e eliminazione
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="⬅️ Precedente", callback_data=f"show_links_prev_{index}"),
            InlineKeyboardButton(text="🗑 Elimina", callback_data=f"delete_link_{index}"),
            InlineKeyboardButton(text="➡️ Successivo", callback_data=f"show_links_next_{index}")
        ],
        [
            InlineKeyboardButton(text="🔙 Menu principale", callback_data="go_main_menu")  # Pulsante per tornare al menu
        ]
    ])

    # Se il messaggio arriva da un callback, modifica il messaggio esistente
    if callback_query:
        await callback_query.answer()
        await bot.edit_message_text(chat_id=chat_id, message_id=callback_query.message.message_id, text=message_text, reply_markup=keyboard)
    else:
        # Se è un comando /list, invia il messaggio
        await bot.send_message(chat_id, message_text, reply_markup=keyboard)



@dp.callback_query(lambda c: c.data == "go_main_menu")
async def go_main_menu_callback(callback_query: types.CallbackQuery):
    chat_id = callback_query.from_user.id
    keyboard = get_main_keyboard()  # Usa la funzione che crea il menu principale
    await bot.edit_message_text(chat_id=chat_id, message_id=callback_query.message.message_id,
                                text="🏠 Sei tornato al menu principale! Scegli un'opzione:", reply_markup=keyboard)




@dp.callback_query(lambda c: c.data == "track_product")
async def track_product_callback(callback_query: types.CallbackQuery):
    await callback_query.answer()  # Risponde alla callback per evitare il messaggio di "caricamento"
    await bot.send_message(callback_query.from_user.id, "📌 Invia il link del prodotto (AliExpress o Amazon) che vuoi monitorare.")



# Callback per "Mostra link" con i pulsanti per la navigazione
@dp.callback_query(lambda c: c.data == "show_links")
async def show_links_callback(callback_query: types.CallbackQuery):
    chat_id = callback_query.from_user.id
    await show_links_with_navigation(chat_id, callback_query)


# Funzione per gestire la navigazione tra i link
@dp.callback_query(lambda c: c.data.startswith("show_links_prev"))
async def show_links_prev(callback_query: types.CallbackQuery):
    chat_id = callback_query.from_user.id
    index = int(callback_query.data.split("_")[-1])

    cursor.execute("SELECT url FROM products WHERE chat_id = ?", (chat_id,))
    urls = cursor.fetchall()

    if index > 0:
        user_links_index[chat_id] = index - 1
    else:
        user_links_index[chat_id] = len(urls) - 1  # Torna all'ultimo link se siamo al primo

    # Ricarica i link da visualizzare
    await show_links_with_navigation(chat_id, callback_query)

@dp.callback_query(lambda c: c.data.startswith("show_links_next"))
async def show_links_next(callback_query: types.CallbackQuery):
    chat_id = callback_query.from_user.id
    index = int(callback_query.data.split("_")[-1])

    cursor.execute("SELECT url FROM products WHERE chat_id = ?", (chat_id,))
    urls = cursor.fetchall()

    if index < len(urls) - 1:
        user_links_index[chat_id] = index + 1
    else:
        user_links_index[chat_id] = 0  # Torna al primo link se siamo all'ultimo

    # Ricarica i link da visualizzare
    await show_links_with_navigation(chat_id, callback_query)


@dp.callback_query(lambda c: c.data.startswith("delete_link"))
async def delete_link_callback(callback_query: types.CallbackQuery):
    chat_id = callback_query.from_user.id
    index = int(callback_query.data.split("_")[-1])

    # Recuperiamo tutti i prodotti dell'utente
    cursor.execute("SELECT id, url FROM products WHERE chat_id = ?", (chat_id,))
    urls = cursor.fetchall()

    if not urls or index >= len(urls):  # Evita accessi fuori limite
        await callback_query.answer("❌ Non ci sono link da eliminare.")
        return

    # Recuperiamo l'ID del prodotto da eliminare
    product_id = urls[index][0]
    cursor.execute("DELETE FROM products WHERE id = ?", (product_id,))
    conn.commit()

    await callback_query.answer("✅ Link eliminato con successo!")

    # Ricarichiamo i link aggiornati dal database
    cursor.execute("SELECT url FROM products WHERE chat_id = ?", (chat_id,))
    remaining_urls = cursor.fetchall()

    if remaining_urls:
        # Se l'elemento cancellato era l'ultimo, spostiamo l'indice all'elemento precedente
        new_index = min(index, len(remaining_urls) - 1)
        user_links_index[chat_id] = new_index
        await show_links_with_navigation(chat_id, callback_query)
    else:
        # Nessun link rimanente, rimuoviamo l'indice
        user_links_index.pop(chat_id, None)
        await bot.edit_message_text(chat_id=chat_id, message_id=callback_query.message.message_id,
                                    text="❌ Non stai monitorando alcun link.")


@dp.callback_query(lambda c: c.data == "help")
async def help_callback(callback_query: types.CallbackQuery):
    help_text = """
    Ecco i comandi disponibili:
    - /start: Inizia la conversazione e mostra il menu principale.
    - /track: Invia un link di un prodotto (AliExpress o Amazon) da monitorare.
    - /list: Visualizza la lista dei prodotti che stai monitorando.
    - /info: Mostra informazioni sul bot.
    - /help: Mostra questo messaggio di aiuto.
    """
    await callback_query.answer()
    await bot.send_message(callback_query.from_user.id, help_text)


# Funzione per ottenere il prezzo da AliExpress e Amazon
def get_price(url):
    try:
        driver.get(url)
        time.sleep(3)  # Attendi che la pagina venga caricata correttamente

        # Gestione link di AliExpress
        if "aliexpress." in url:
            price_element = driver.find_element(By.CSS_SELECTOR, ".product-price-value")
            price = price_element.text.replace("€", "").strip()

        # Gestione link di Amazon
        elif "amazon." in url:
            # Aspetta che l'elemento del prezzo sia visibile
            price_element = driver.find_element(By.CSS_SELECTOR, ".a-price-whole")
            price = price_element.text.replace("$", "").strip()

        else:
            return None  # Non gestiamo altri tipi di link per ora

        return float(price.replace(",", "."))  # Rimuove eventuali virgole e converte in float
    except Exception as e:
        logging.error(f"Errore durante il recupero del prezzo: {e}")
        return None


# Controllo periodico dei prezzi
async def check_prices_periodically():
    while True:
        cursor.execute("SELECT id, chat_id, url, price FROM products")
        products = cursor.fetchall()

        for product in products:
            product_id, chat_id, url, old_price = product
            new_price = get_price(url)

            if new_price is not None and new_price != old_price:
                await bot.send_message(chat_id=chat_id, text=f"🔔 Il prezzo per il prodotto {url} è cambiato! Nuovo prezzo: {new_price}€")
                cursor.execute("UPDATE products SET price = ? WHERE id = ?", (new_price, product_id))
                conn.commit()

        await asyncio.sleep(600)  # Controllo ogni 5 minuti

# Creazione della tastiera principale
def get_main_keyboard():
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="Monitora un prodotto", callback_data="track_product"),
            InlineKeyboardButton(text="Visualizza prodotti monitorati", callback_data="show_links")
        ],
        [
            InlineKeyboardButton(text="Help", callback_data="help")
        ]
    ])
    return keyboard


# --- SEZIONE COMANDI ---
@dp.message(Command("start"))
async def start(message: types.Message):
    chat_id = message.chat.id
    cursor.execute("INSERT OR IGNORE INTO users (chat_id) VALUES (?)", (chat_id,))
    conn.commit()
    keyboard = get_main_keyboard()
    await message.answer("Benvenuto su SpyPyPriceBot! Scegli una delle opzioni qui sotto:", reply_markup=keyboard)

@dp.message(Command("track"))
async def track_product_command(message: types.Message):
    await message.answer("📌 Invia il link del prodotto (AliExpress o Amazon) che vuoi monitorare.")

@dp.message(Command("list"))
async def show_links_command(message: types.Message):
    chat_id = message.chat.id
    await show_links_with_navigation(chat_id)

@dp.message(Command("info"))
async def bot_info(message: types.Message):
    info_text = """
    SpyPyPriceBot è un bot creato per monitorare i prezzi dei prodotti su AliExpress e Amazon.
    - Versione: 1.0
    - Autore: []
    """
    await message.answer(info_text)

# Aggiungi il comando help
@dp.message(Command("help"))
async def help_command(message: types.Message):
    help_text = """
    Ecco i comandi disponibili:
    - /start: Inizia la conversazione e mostra il menu principale.
    - /track: Invia un link di un prodotto (AliExpress o Amazon) da monitorare.
    - /list: Visualizza la lista dei prodotti che stai monitorando.
    - /info: Mostra informazioni sul bot.
    - /help: Mostra questo messaggio di aiuto.
    """
    await message.answer(help_text)

# --- SOLO ALLA FINE, METTIAMO IL GESTORE GENERICO ---
# Gestione dei link inviati dall'utente
@dp.message()
async def handle_message(message: types.Message):
    chat_id = message.chat.id
    url = message.text.strip()

    # Controlla se il messaggio è un link valido di AliExpress o Amazon
    if "aliexpress." not in url and "amazon." not in url:
        await message.answer("❌ Devi fornire un link valido di AliExpress o Amazon. Esempio:\nhttps://www.aliexpress.com/item/xxxxx o https://www.amazon.com/dp/xxxxx")
        return

    cursor.execute("SELECT id, price FROM products WHERE chat_id = ? AND url = ?", (chat_id, url))
    existing_product = cursor.fetchone()

    if existing_product:
        product_id, old_price = existing_product
        new_price = get_price(url)

        if new_price is not None:
            if new_price != old_price:
                cursor.execute("UPDATE products SET price = ?, last_checked = ? WHERE id = ?", (new_price, int(time.time()), product_id))
                conn.commit()
                await message.answer(f"✅ Il prezzo è stato aggiornato: {new_price}€\nTi avviserò se cambia!")
            else:
                await message.answer("🔔 Il prezzo non è cambiato.")
        else:
            await message.answer("❌ Errore nel recupero del prezzo. Assicurati che il link sia corretto!")
    else:
        new_price = get_price(url)
        if new_price is not None:
            cursor.execute("INSERT INTO products (chat_id, url, price, last_checked) VALUES (?, ?, ?, ?)", (chat_id, url, new_price, int(time.time())))
            conn.commit()
            await message.answer(f"✅ Prezzo attuale registrato: {new_price}€\nTi avviserò se cambia!")
        else:
            await message.answer("❌ Errore nel recupero del prezzo. Assicurati che il link sia corretto!")


# --- MAIN ---
async def main():
    logging.basicConfig(level=logging.INFO)
    await bot.delete_webhook(drop_pending_updates=True)
    asyncio.create_task(check_prices_periodically())
    await dp.start_polling(bot)

if __name__ == "__main__":
    try:
        asyncio.run(main())
    finally:
        driver.quit()
        conn.close()
