from telegram import (
    Update,
    InlineKeyboardButton,
    InlineKeyboardMarkup
)
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    MessageHandler,
    ConversationHandler,
    CallbackQueryHandler,
    ContextTypes,
    filters
)
import sqlite3
import logging

# =========================
# BOT SETTINGS
# =========================
TOKEN = "8262325261:AAE9AZxLY_GEPN-Bqn32iqofdoQ5xtfSP9A"
ADMIN_ID = 8190068599   # admin chat id

# =========================
# LOGGING
# =========================
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO
)

# =========================
# DATABASE CREATE
# =========================
DB_FILE = "users.db"
conn = sqlite3.connect(DB_FILE)
c = conn.cursor()
c.execute("""CREATE TABLE IF NOT EXISTS users (
    chat_id INTEGER PRIMARY KEY,
    utr TEXT,
    name TEXT,
    whatsapp TEXT,
    screenshot TEXT,
    status TEXT
)""")
conn.commit()
conn.close()

# =========================
# STATES
# =========================
ASK_SCREENSHOT, ASK_UTR, ASK_NAME, ASK_WHATSAPP = range(4)

# =========================
# START COMMAND
# =========================
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("🙏 స్వాగతం!\n\nదయచేసి ముందుగా మీ *పేమెంట్ స్క్రీన్‌షాట్* పంపండి.")
    return ASK_SCREENSHOT

# =========================
# STEP 1 - SCREENSHOT
# =========================
async def ask_screenshot(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message.photo:
        await update.message.reply_text("❌ దయచేసి *స్క్రీన్‌షాట్ ఫోటో* మాత్రమే పంపండి.")
        return ASK_SCREENSHOT

    file_id = update.message.photo[-1].file_id
    context.user_data["screenshot"] = file_id
    context.user_data["chat_id"] = update.message.chat_id
    context.user_data["username"] = update.message.from_user.username
    context.user_data["firstname"] = update.message.from_user.first_name

    await update.message.reply_text("✅ Screenshot వచ్చింది.\n\nఇప్పుడు మీ *12 అంకెల UTR నంబర్* ఇవ్వండి.")
    return ASK_UTR

# =========================
# STEP 2 - UTR
# =========================
async def ask_utr(update: Update, context: ContextTypes.DEFAULT_TYPE):
    utr = update.message.text.strip()
    if not utr.isdigit() or len(utr) != 12:
        await update.message.reply_text("❌ సరైన *12 అంకెల UTR నంబర్* ఇవ్వండి.")
        return ASK_UTR

    context.user_data["utr"] = utr
    await update.message.reply_text("✅ UTR వచ్చింది.\n\nఇప్పుడు మీ *బ్యాంక్ హోల్డర్ పేరు* ఇవ్వండి.")
    return ASK_NAME

# =========================
# STEP 3 - NAME
# =========================
async def ask_name(update: Update, context: ContextTypes.DEFAULT_TYPE):
    name = update.message.text.strip()
    context.user_data["name"] = name

    await update.message.reply_text("✅ పేరు వచ్చింది.\n\nఇప్పుడు మీ *10 అంకెల WhatsApp నంబర్* ఇవ్వండి.")
    return ASK_WHATSAPP

# =========================
# STEP 4 - WHATSAPP
# =========================
async def ask_whatsapp(update: Update, context: ContextTypes.DEFAULT_TYPE):
    whatsapp = update.message.text.strip()
    if not whatsapp.isdigit() or len(whatsapp) != 10:
        await update.message.reply_text("❌ *10 అంకెల WhatsApp నంబర్* ఇవ్వండి.")
        return ASK_WHATSAPP

    context.user_data["whatsapp"] = whatsapp

    # డేటాబేస్ లో సేవ్ చేయడం
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute("INSERT OR REPLACE INTO users (chat_id, utr, name, whatsapp, screenshot, status) VALUES (?,?,?,?,?,?)",
              (context.user_data["chat_id"],
               context.user_data["utr"],
               context.user_data["name"],
               whatsapp,
               context.user_data["screenshot"],
               "pending"))
    conn.commit()
    conn.close()

    # ADMIN కి పంపడం
    keyboard = [
        [
            InlineKeyboardButton("✅ Approve", callback_data=f"approve_{context.user_data['chat_id']}"),
            InlineKeyboardButton("❌ Reject", callback_data=f"reject_{context.user_data['chat_id']}")
        ]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    username = context.user_data.get("username", "N/A")
    firstname = context.user_data.get("firstname", "N/A")

    await context.bot.send_photo(
        chat_id=ADMIN_ID,
        photo=context.user_data["screenshot"],
        caption=(
            f"🔔 కొత్త సబ్మిషన్ వచ్చింది:\n\n"
            f"👤 పేరు: {context.user_data['name']}\n"
            f"💰 UTR: {context.user_data['utr']}\n"
            f"🏦 బ్యాంక్ హోల్డర్: {context.user_data['name']}\n"
            f"📱 WhatsApp: {whatsapp}\n\n"
            f"📌 User: @{username}\n"
            f"🆔 Chat ID: {context.user_data['chat_id']}\n"
            f"👤 First Name: {firstname}"
        ),
        reply_markup=reply_markup
    )

    await update.message.reply_text("✅ మీ సబ్మిషన్ అడ్మిన్ కి పంపబడింది.\n⏳ వెరిఫై అయిన తరువాత మీకు మెసేజ్ వస్తుంది.")
    return ConversationHandler.END

# =========================
# ADMIN APPROVE / REJECT
# =========================
async def button(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    data = query.data

    if data.startswith("approve_"):
        chat_id = int(data.split("_")[1])
        await context.bot.send_message(chat_id, "✅ మీ సబ్మిషన్ *అప్రూవ్* చేయబడింది!")
        await query.edit_message_caption(query.message.caption + "\n\n✅ Approved by Admin")

    elif data.startswith("reject_"):
        chat_id = int(data.split("_")[1])
        await context.bot.send_message(chat_id, "❌ మీ సబ్మిషన్ *రిజెక్ట్* చేయబడింది.")
        await query.edit_message_caption(query.message.caption + "\n\n❌ Rejected by Admin")

# =========================
# MAIN
# =========================
def main():
    app = ApplicationBuilder().token(TOKEN).build()

    conv_handler = ConversationHandler(
        entry_points=[CommandHandler("start", start)],
        states={
            ASK_SCREENSHOT: [MessageHandler(filters.PHOTO, ask_screenshot)],
            ASK_UTR: [MessageHandler(filters.TEXT & ~filters.COMMAND, ask_utr)],
            ASK_NAME: [MessageHandler(filters.TEXT & ~filters.COMMAND, ask_name)],
            ASK_WHATSAPP: [MessageHandler(filters.TEXT & ~filters.COMMAND, ask_whatsapp)],
        },
        fallbacks=[]
    )

    app.add_handler(conv_handler)
    app.add_handler(CallbackQueryHandler(button))

    print("🤖 Bot is running...")
    app.run_polling()

if __name__ == "__main__":
    main()
