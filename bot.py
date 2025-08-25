from telegram import Update
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    MessageHandler,
    ConversationHandler,
    ContextTypes,
    filters
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
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
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

    await update.message.reply_text("💎 Send your payment screenshot 📸")
    return ASK_SCREENSHOT

# Screenshot handler
async def ask_utr(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message.photo:
        await update.message.reply_text("❌ Please send your payment screenshot.")
        return ASK_SCREENSHOT

    context.user_data["screenshot"] = update.message.photo[-1].file_id
    await update.message.reply_text("💰 Enter your 12-digit UTR number")
    return ASK_UTR

# UTR handler
async def ask_name(update: Update, context: ContextTypes.DEFAULT_TYPE):
    utr = update.message.text.strip()
    if not utr.isdigit() or len(utr) != 12:
        await update.message.reply_text("❌ Invalid UTR number. Must be 12 digits.")
        return ASK_UTR

    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute("SELECT * FROM users WHERE utr=?", (utr,))
    if c.fetchone():
        await update.message.reply_text("❌ This UTR number is already submitted. Use /start again.")
        conn.close()
        return ConversationHandler.END
    conn.close()

    context.user_data["utr"] = utr
    await update.message.reply_text("📝 Enter your full name")
    return ASK_NAME

# Name handler
async def ask_whatsapp(update: Update, context: ContextTypes.DEFAULT_TYPE):
    name = update.message.text.strip()
    context.user_data["name"] = name
    await update.message.reply_text("📱 Enter your WhatsApp number")
    return ASK_WHATSAPP

# WhatsApp handler
async def save_data(update: Update, context: ContextTypes.DEFAULT_TYPE):
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

    await update.message.reply_text("✅ Your details are saved. Admin will contact you soon.")
    return ConversationHandler.END

# Cancel handler
async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("❌ Operation cancelled.")
    return ConversationHandler.END

# Main function
def main():
    init_db()
    app = ApplicationBuilder().token(BOT_TOKEN).build()

    conv_handler = ConversationHandler(
        entry_points=[CommandHandler('start', start)],
        states={
            ASK_SCREENSHOT: [MessageHandler(filters.PHOTO, ask_utr)],
            ASK_UTR: [MessageHandler(filters.TEXT & ~filters.COMMAND, ask_name)],
            ASK_NAME: [MessageHandler(filters.TEXT & ~filters.COMMAND, ask_whatsapp)],
            ASK_WHATSAPP: [MessageHandler(filters.TEXT & ~filters.COMMAND, save_data)],
        },
        fallbacks=[CommandHandler('cancel', cancel)],
    )

    app.add_handler(conv_handler)

    app.run_polling()

if __name__ == '__main__':
    main()
