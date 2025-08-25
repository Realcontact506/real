from telegram import Update
from telegram.ext import Updater, CommandHandler, MessageHandler, Filters, ConversationHandler, CallbackContext
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

def start(update: Update, context: CallbackContext):
    user = update.message.from_user
    chat_id = update.message.chat_id
    username = user.username or ""
    first_name = user.first_name or ""
    last_name = user.last_name or ""

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

def ask_utr(update: Update, context: CallbackContext):
    if not update.message.photo:
        update.message.reply_text("❌ Please send your payment screenshot.")
        return ASK_SCREENSHOT

    context.user_data["screenshot"] = update.message.photo[-1].file_id
    update.message.reply_text("💰 Enter your 12-digit UTR number")
    return ASK_UTR

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
    update.message.reply_text("📝 Enter your full name")
    return ASK_NAME

def ask_whatsapp(update: Update, context: CallbackContext):
    name = update.message.text.strip()
    context.user_data["name"] = name
    update.message.reply_text("📱 Enter your WhatsApp number")
    return ASK_WHATSAPP

def save_data(update: Update, context: CallbackContext):
    whatsapp = update.message.text.strip()
    context.user_data["whatsapp"] = whatsapp

    chat_id = update.message.chat_id
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute(
        "UPDATE users SET utr=?, name=?, whatsapp=?, screenshot=?, status=? WHERE chat_id=?",
        (
            context.user_data["utr"],
            context.user_data["name"],
            context.user_data["whatsapp"],
            context.user_data["screenshot"],
            "pending",
            chat_id
        )
    )
    conn.commit()
    conn.close()

    update.message.reply_text("✅ Your details are saved. Admin will contact you soon.")
    return ConversationHandler.END

def cancel(update: Update, context: CallbackContext):
    update.message.reply_text("❌ Operation cancelled.")
    return ConversationHandler.END

def main():
    init_db()
    updater = Updater(BOT_TOKEN, use_context=True)
    dp = updater.dispatcher

    conv_handler = ConversationHandler(
        entry_points=[CommandHandler('start', start)],
        states={
            ASK_SCREENSHOT: [MessageHandler(Filters.photo, ask_utr)],
            ASK_UTR: [MessageHandler(Filters.text & ~Filters.command, ask_name)],
            ASK_NAME: [MessageHandler(Filters.text & ~Filters.command, ask_whatsapp)],
            ASK_WHATSAPP: [MessageHandler(Filters.text & ~Filters.command, save_data)],
        },
        fallbacks=[CommandHandler('cancel', cancel)],
    )

    dp.add_handler(conv_handler)

    updater.start_polling()
    updater.idle()

if __name__ == '__main__':
    main()
