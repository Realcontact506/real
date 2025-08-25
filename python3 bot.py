from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    Updater,
    CommandHandler,
    MessageHandler,
    Filters,
    ConversationHandler,
    CallbackQueryHandler,
    CallbackContext,
)
import sqlite3

# Bot Token & Admin ID
BOT_TOKEN = "8262325261:AAE9AZxLY_GEPN-Bqn32iqofdoQ5xtfSP9A"
ADMIN_ID = 8190068599

# Database setup
DB_FILE = "bot_database.sqlite"

def init_db():
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            chat_id INTEGER UNIQUE,
            username TEXT,
            first_name TEXT,
            last_name TEXT,
            utr TEXT UNIQUE,
            name TEXT,
            whatsapp TEXT,
            screenshot TEXT,
            status TEXT
        )
    ''')
    conn.commit()
    conn.close()

# States
ASK_SCREENSHOT, ASK_UTR, ASK_NAME, ASK_WHATSAPP = range(4)

# /start -> automatic DB add
def start(update: Update, context: CallbackContext):
    user = update.message.from_user
    chat_id = update.message.chat_id
    username = user.username or ""
    first_name = user.first_name or ""
    last_name = user.last_name or ""

    # Save user to DB automatically
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute(
        "INSERT OR IGNORE INTO users (chat_id, username, first_name, last_name, status) VALUES (?, ?, ?, ?, ?)",
        (chat_id, username, first_name, last_name, "pending")
    )
    conn.commit()
    conn.close()

    update.message.reply_text("💎 Send your payment screenshot 📸")
    return ASK_SCREENSHOT

# Screenshot
def ask_utr(update: Update, context: CallbackContext):
    if not update.message.photo:
        update.message.reply_text("❌ Please send your payment screenshot.")
        return ASK_SCREENSHOT

    context.user_data["screenshot"] = update.message.photo[-1].file_id
    context.user_data["chat_id"] = update.message.chat_id
    update.message.reply_text("💰 Enter your 12-digit UTR number")
    return ASK_UTR

# UTR
def ask_name(update: Update, context: CallbackContext):
    utr = update.message.text.strip()
    if not utr.isdigit() or len(utr) != 12:
        update.message.reply_text("❌ Invalid UTR number. Must be 12 digits.")
        return ASK_UTR

    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute("SELECT * FROM users WHERE utr=?", (utr,))
    if c.fetchone():
        update.message.reply_text("❌ This UTR number is already submitted. Use /start again.")
        conn.close()
        return ConversationHandler.END
    conn.close()

    context.user_data["utr"] = utr
    update.message.re
