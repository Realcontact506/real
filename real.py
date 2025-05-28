import os
import logging
from telegram import Update
from telegram.ext import ApplicationBuilder, ContextTypes, CommandHandler, MessageHandler, filters
from supabase import create_client

# Supabase credentials
SUPABASE_URL = "https://skorflvwergngsupnlzu.supabase.co"
SUPABASE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InNrb3JmbHZ3ZXJnbmdzdXBubHp1Iiwicm9sZSI6ImFub24iLCJpYXQiOjE3NDg0MzM0ODEsImV4cCI6MjA2NDAwOTQ4MX0.1KYYRjph_8ZH2BJ3vSVSJuuOdnB18VBO37iDrJ0We54"
supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

# Bot Token
BOT_TOKEN = "8118983802:AAFp3D8zgxjgJHDndAQRYEzlOmsC4mpWnGE"

# Logging
logging.basicConfig(level=logging.INFO)
user_states = {}

# /start command
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("ఫోటో స్క్రీన్‌షాట్ ని పంపండి. దానికి తర్వాత UTR నెంబర్ అడుగుతాను.")

# Photo handler
async def handle_photo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = str(update.message.from_user.id)
    photo = update.message.photo[-1]
    photo_file = await context.bot.get_file(photo.file_id)

    print("📸 Photo received")  # Debug message

    if not os.path.exists("filedownloads"):
        os.makedirs("filedownloads")

    file_path = f"filedownloads/{user_id}.jpg"
    await photo_file.download_to_drive(file_path)  # ✅ Correct method

    user_states[user_id] = {"step": "waiting_for_utr", "screenshot_path": file_path}
    await update.message.reply_text("ధన్యవాదాలు. ఇప్పుడు మీ UTR నెంబర్ పంపండి.")

# Text message handler (UTR)
async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = str(update.message.from_user.id)
    text = update.message.text

    if user_id in user_states and user_states[user_id]["step"] == "waiting_for_utr":
        screenshot_path = user_states[user_id]["screenshot_path"]

        supabase.table("contacts").insert({
            "user_id": user_id,
            "utr": text,
            "screenshot_url": screenshot_path,
            "status": "pending",
            "contact_number": "",
        }).execute()

        user_states.pop(user_id)
        await update.message.reply_text("మీ UTR సేవ్ అయింది. త్వరలో వెరిఫై చేసి మేము మీకు నెంబర్ పంపుతాం.")
    else:
        result = supabase.table("contacts").select("*").eq("user_id", user_id).eq("status", "approved").execute()
        if result.data and len(result.data) > 0:
            contact = result.data[0]["contact_number"]
            await update.message.reply_text(f"మీకు కాంటాక్ట్ నెంబర్: {contact}")
        else:
            await update.message.reply_text("మీ డేటా ఇంకా వెరిఫై కాలేదు. దయచేసి కొద్దిసేపటికి మళ్లీ చెక్ చేయండి.")

# Main function
def main():
    app = ApplicationBuilder().token(BOT_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.PHOTO, handle_photo))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    print("🤖 Bot Running...")
    app.run_polling()

if __name__ == "__main__":
    main()
