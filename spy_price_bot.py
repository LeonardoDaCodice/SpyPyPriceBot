import asyncio
import time
import os
import logging
import sqlite3
import re
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

bot = Bot(token=TOKEN)
dp = Dispatcher()

user_links_index = {}

chrome_options = Options()
chrome_options.add_argument("--headless")
chrome_options.add_argument("--disable-gpu")
chrome_options.add_argument("--no-sandbox")
chrome_options.add_argument("--disable-dev-shm-usage")

service = Service(ChromeDriverManager().install())
driver = webdriver.Chrome(service=service, options=chrome_options)

conn = sqlite3.connect("prices.db", check_same_thread=False)
cursor = conn.cursor()

cursor.execute("""
    CREATE TABLE IF NOT EXISTS products (
        id INTEGER PRIMARY KEY, 
        chat_id INTEGER, 
        url TEXT, 
        price FLOAT, 
        last_checked TIMESTAMP,
        target_price FLOAT
    )
""")

cursor.execute("""
    CREATE TABLE IF NOT EXISTS users (
        chat_id INTEGER PRIMARY KEY
    )
""")
conn.commit()

# --- MENU PRINCIPALE ---
def get_main_keyboard():
    return InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="🛒 Monitora un prodotto", callback_data="track_product"),
            InlineKeyboardButton(text="📋 Visualizza prodotti monitorati", callback_data="show_links")
        ],
        [
            InlineKeyboardButton(text="❓ Help", callback_data="help")
        ]
    ])


# --- CALLBACK PER MONITORAGGIO ---
@dp.callback_query(lambda c: c.data == "monitor_all")
async def monitor_all_callback(callback_query: types.CallbackQuery):
    chat_id = callback_query.from_user.id

    if chat_id not in user_links_index:
        await callback_query.message.edit_text("⚠️ Nessun link trovato. Riprova l'invio del link.")
        return

    url = user_links_index.get(chat_id)

    # 👇 Mostra un messaggio iniziale di caricamento
    loading_msg = await bot.send_message(chat_id, "⏳ Sto impostando il monitoraggio...")

    cursor.execute("SELECT 1 FROM products WHERE chat_id = ? AND url = ?", (chat_id, url))
    if cursor.fetchone():
        await bot.edit_message_text(chat_id=chat_id, message_id=loading_msg.message_id,
                                    text="⚠️ Questo prodotto è già monitorato, eliminalo dalla lista se vuoi modificare la modalità di monitoraggio")
        return

    new_price = get_price(url)
    if new_price is None:
        await bot.edit_message_text(chat_id=chat_id, message_id=loading_msg.message_id,
                                    text="❌ Errore nel recupero del prezzo.")
        return

    cursor.execute("INSERT INTO products (chat_id, url, price, last_checked, target_price) VALUES (?, ?, ?, ?, NULL)",
                   (chat_id, url, new_price, int(time.time())))
    conn.commit()

    await bot.edit_message_text(chat_id=chat_id, message_id=loading_msg.message_id,
                                text=f"✅ Prezzo attuale registrato: {new_price}€\nTi avviserò per ogni variazione!")
    user_links_index.pop(chat_id, None)


@dp.callback_query(lambda c: c.data == "monitor_target")
async def monitor_target_callback(callback_query: types.CallbackQuery):
    chat_id = callback_query.from_user.id
    if chat_id not in user_links_index:
        await callback_query.message.edit_text("⚠️ Nessun link trovato. Riprova l'invio del link.")
        return
    await callback_query.message.edit_text("🎯 Invia ora il prezzo target (es: 49.99)")

@dp.callback_query(lambda c: c.data == "track_product")
async def track_product_callback(callback_query: types.CallbackQuery):
    await callback_query.answer()
    await bot.send_message(callback_query.from_user.id, "📌 Invia il link del prodotto (AliExpress o Amazon) che vuoi monitorare.")

@dp.callback_query(lambda c: c.data == "help")
async def help_callback(callback_query: types.CallbackQuery):
    await callback_query.answer()
    await bot.send_message(callback_query.from_user.id, """
Ecco i comandi disponibili:
- /start: Inizia la conversazione e mostra il menu principale.
- /track: Invia un link di un prodotto (AliExpress o Amazon) da monitorare.
- /list: Visualizza la lista dei prodotti che stai monitorando.
- /info: Mostra informazioni sul bot.
- /help: Mostra questo messaggio di aiuto.
""")

@dp.callback_query(lambda c: c.data == "show_links")
async def show_links_callback(callback_query: types.CallbackQuery):
    chat_id = callback_query.from_user.id
    await show_links_with_navigation(chat_id, callback_query)

@dp.callback_query(lambda c: c.data.startswith("show_links_prev"))
async def show_links_prev(callback_query: types.CallbackQuery):
    chat_id = callback_query.from_user.id
    index = int(callback_query.data.split("_")[-1])
    cursor.execute("SELECT url FROM products WHERE chat_id = ?", (chat_id,))
    urls = cursor.fetchall()
    if not urls:
        await callback_query.message.edit_text("❌ Non ci sono link da mostrare.")
        return
    user_links_index[chat_id] = index - 1 if index > 0 else len(urls) - 1
    await show_links_with_navigation(chat_id, callback_query)

@dp.callback_query(lambda c: c.data.startswith("show_links_next"))
async def show_links_next(callback_query: types.CallbackQuery):
    chat_id = callback_query.from_user.id
    index = int(callback_query.data.split("_")[-1])
    cursor.execute("SELECT url FROM products WHERE chat_id = ?", (chat_id,))
    urls = cursor.fetchall()
    if not urls:
        await callback_query.message.edit_text("❌ Non ci sono link da mostrare.")
        return
    user_links_index[chat_id] = index + 1 if index < len(urls) - 1 else 0
    await show_links_with_navigation(chat_id, callback_query)

@dp.callback_query(lambda c: c.data.startswith("delete_link"))
async def delete_link_callback(callback_query: types.CallbackQuery):
    chat_id = callback_query.from_user.id
    index = int(callback_query.data.split("_")[-1])
    cursor.execute("SELECT id FROM products WHERE chat_id = ?", (chat_id,))
    urls = cursor.fetchall()
    if not urls or index >= len(urls):
        await callback_query.answer("❌ Nessun link da eliminare.")
        return
    product_id = urls[index][0]
    cursor.execute("DELETE FROM products WHERE id = ?", (product_id,))
    conn.commit()
    await callback_query.answer("✅ Link eliminato con successo!")
    cursor.execute("SELECT url FROM products WHERE chat_id = ?", (chat_id,))
    remaining = cursor.fetchall()
    if remaining:
        user_links_index[chat_id] = min(index, len(remaining) - 1)
        await show_links_with_navigation(chat_id, callback_query)
    else:
        user_links_index.pop(chat_id, None)
        await bot.edit_message_text(chat_id=chat_id, message_id=callback_query.message.message_id, text="❌ Non stai monitorando alcun link.")

@dp.callback_query(lambda c: c.data == "go_main_menu")
async def go_main_menu_callback(callback_query: types.CallbackQuery):
    keyboard = get_main_keyboard()
    await bot.edit_message_text(chat_id=callback_query.from_user.id, message_id=callback_query.message.message_id,
                                text="🏠 Sei tornato al menu principale! Scegli un'opzione:", reply_markup=keyboard)

@dp.message(Command("start"))
async def start(message: types.Message):
    chat_id = message.chat.id
    cursor.execute("INSERT OR IGNORE INTO users (chat_id) VALUES (?)", (chat_id,))
    conn.commit()
    await message.answer("👋Benvenuto su 🕵️‍♂️SpyPyPriceBot🤖! Scegli una delle opzioni qui sotto:", reply_markup=get_main_keyboard())

@dp.message(Command("track"))
async def track_command(message: types.Message):
    await message.answer("📌 Invia il link del prodotto (AliExpress o Amazon) che vuoi monitorare.")

@dp.message(Command("list"))
async def list_command(message: types.Message):
    await show_links_with_navigation(message.chat.id)

@dp.message(Command("info"))
async def info_command(message: types.Message):
    await message.answer("""
SpyPyPriceBot è un bot creato per monitorare i prezzi dei prodotti su AliExpress e Amazon.
- Versione: 1.0
- Autore: []
""")

@dp.message(Command("help"))
async def help_command(message: types.Message):
    await message.answer("""
Ecco i comandi disponibili:
- /start: Inizia la conversazione e mostra il menu principale.
- /track: Invia un link di un prodotto (AliExpress o Amazon) da monitorare.
- /list: Visualizza la lista dei prodotti che stai monitorando.
- /info: Mostra informazioni sul bot.
- /help: Mostra questo messaggio di aiuto.
""")

# --- FUNZIONE PREZZI ---
def get_price(url):
    try:
        driver.get(url)
        time.sleep(3)

        if "aliexpress." in url:
            price_element = driver.find_element(By.CSS_SELECTOR, ".product-price-value")
            price = price_element.text.replace("€", "").strip()
            return float(price.replace(",", "."))

        elif "amazon." in url or "amzn." in url:
            whole = driver.find_element(By.CSS_SELECTOR, ".a-price-whole").text
            fraction = driver.find_element(By.CSS_SELECTOR, ".a-price-fraction").text
            price = f"{whole}.{fraction}"
            return float(price.replace(",", "").replace(" ", ""))  # rimuove eventuali spazi o separatori

        else:
            return None

    except Exception as e:
        logging.error(f"Errore recupero prezzo: {e}")
        return None

# --- CHECK PERIODICO ---
async def check_prices_periodically():
    while True:
        cursor.execute("SELECT id, chat_id, url, price FROM products")
        for product_id, chat_id, url, old_price in cursor.fetchall():
            new_price = get_price(url)
            cursor.execute("SELECT target_price FROM products WHERE id = ?", (product_id,))
            target = cursor.fetchone()[0]
            if new_price is not None:
                if target is not None and new_price <= target:
                    msg = (
                        f'🎯 <b>Prezzo target raggiunto!</b>\n'
                        f'<a href="{url}">Visualizza prodotto</a>\n'
                        f'🎯 Target: {target}€\n'
                        f'💰 Attuale: {new_price}€\n\n'
                        f'🗑 Il prodotto è stato rimosso automaticamente dal monitoraggio.'
                    )
                    await bot.send_message(chat_id, msg, parse_mode="HTML")
                    cursor.execute("DELETE FROM products WHERE id = ?", (product_id,))
                    conn.commit()
                elif new_price != old_price and target is None:
                    arrow = "🟢⬇️" if new_price < old_price else "🔴⬆️"
                    change = "diminuito" if new_price < old_price else "aumentato"
                    msg = f'🔔 Il prezzo di <a href="{url}">questo prodotto</a> è cambiato!\n{arrow} <b>È {change}!</b>\n<s>💰 Prima: {old_price}€</s>\n💰 Ora: {new_price}€'
                    await bot.send_message(chat_id, msg, parse_mode="HTML")
                    cursor.execute("UPDATE products SET price = ? WHERE id = ?", (new_price, product_id))
                    conn.commit()
        await asyncio.sleep(600)


# --- VISUALIZZAZIONE LINK MONITORATI ---
async def show_links_with_navigation(chat_id, callback_query=None):
    cursor.execute("SELECT url, price, target_price FROM products WHERE chat_id = ?", (chat_id,))
    products = cursor.fetchall()

    if not products:
        if callback_query:
            await callback_query.answer()
        await bot.send_message(chat_id, "❌ Non stai monitorando alcun link.")
        return

    index = user_links_index.get(chat_id, 0)
    if index >= len(products):
        index = 0
        user_links_index[chat_id] = 0

    current_url, current_price, target_price = products[index]
    message_text = f"🔗 Link monitorato {index + 1} di {len(products)}:\n[Link di riferimento al prodotto]({current_url})\n💰 Prezzo: €{current_price}"
    if target_price is not None:
        message_text += f"\n🎯 Prezzo target: €{target_price}"
    else:
        message_text += f"\n📈 Monitoro tutte le variazioni"

    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="⬅️ Precedente", callback_data=f"show_links_prev_{index}"),
            InlineKeyboardButton(text="🗑 Elimina", callback_data=f"delete_link_{index}"),
            InlineKeyboardButton(text="➡️ Successivo", callback_data=f"show_links_next_{index}")
        ],
        [
            InlineKeyboardButton(text="🔙 Menu principale", callback_data="go_main_menu")
        ]
    ])

    if callback_query:
        await callback_query.answer()
        try:
            await bot.edit_message_text(
                chat_id=chat_id,
                message_id=callback_query.message.message_id,
                text=message_text,
                reply_markup=keyboard,
                parse_mode='Markdown'
            )
        except Exception as e:
            if "message is not modified" in str(e):
                pass
            else:
                raise
    else:
        await bot.send_message(chat_id, message_text, reply_markup=keyboard, parse_mode='Markdown')

# --- HANDLE MESSAGGI GENERICI (verifica se è un link o un prezzo target) ---
@dp.message()
async def handle_message(message: types.Message):
    chat_id = message.chat.id
    text = message.text.strip()

    # Caso: L'utente ha appena inviato un prezzo target
    if chat_id in user_links_index and isinstance(user_links_index[chat_id], str) and user_links_index[chat_id].startswith("http"):
        if not re.match(r'^\d+[.,]?\d*$', text):
            await message.answer("❌ Il prezzo deve essere un numero valido (es: 49.99)")
            return
        try:
            loading_msg = await message.answer("⏳ Impostazione del prezzo target in corso...")

            target_price = float(text.replace(",", "."))
            url = user_links_index[chat_id]
            new_price = get_price(url)

            if new_price is None:
                await bot.edit_message_text(chat_id=chat_id, message_id=loading_msg.message_id,
                                            text="❌ Errore nel recupero del prezzo.")
                user_links_index.pop(chat_id, None)
                return

            if target_price >= new_price:
                await bot.edit_message_text(
                    chat_id=chat_id,
                    message_id=loading_msg.message_id,
                    text=f"⚠️ Il prezzo attuale è già inferiore o uguale al target inserito.\n"
                         f"💰 Prezzo attuale: {new_price}€\n🎯 Target: {target_price}€\n"
                         f"Inserisci un target più basso."
                )
                return

            cursor.execute("INSERT INTO products (chat_id, url, price, last_checked, target_price) VALUES (?, ?, ?, ?, ?)",
                           (chat_id, url, new_price, int(time.time()), target_price))
            conn.commit()
            await bot.edit_message_text(
                chat_id=chat_id,
                message_id=loading_msg.message_id,
                text=f"✅ Prodotto monitorato con prezzo target di {target_price}€!\nPrezzo attuale: {new_price}€"
            )
            user_links_index.pop(chat_id, None)
        except ValueError:
            await message.answer("❌ Inserisci un numero valido (es: 49.99)")
        return

    # Caso: Il messaggio non è un link valido
    if "aliexpress." not in text and "amazon." not in text and "amzn." not in text:
        await message.answer("❌ Devi fornire un link valido di AliExpress o Amazon.")
        return

    # Controlla se il link è già monitorato
    cursor.execute("SELECT 1 FROM products WHERE chat_id = ? AND url = ?", (chat_id, text))
    if cursor.fetchone():
        await message.answer("⚠️ Questo prodotto è già monitorato, eliminalo dalla lista se vuoi modificare la modalità di monitoraggio")
        return

    # Mostra i pulsanti di scelta modalità di monitoraggio
    loading = await message.answer("🔄 Recupero informazioni, attendi...")
    user_links_index[chat_id] = text
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="📉 Monitora tutte le variazioni", callback_data="monitor_all"),
            InlineKeyboardButton(text="🎯 Monitora con prezzo target", callback_data="monitor_target")
        ]
    ])
    await loading.edit_text(f"🔗 Link ricevuto correttamente:\n{text}\n\nCome vuoi monitorarlo?", reply_markup=keyboard)


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
