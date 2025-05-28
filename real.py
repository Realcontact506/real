# Handle Screenshot
async def handle_photo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = str(update.message.from_user.id)
    photo = update.message.photo[-1]
    
    # Get file object
    photo_file = await context.bot.get_file(photo.file_id)

    if not os.path.exists("filedownloads"):
        os.makedirs("filedownloads")
    
    file_path = f"filedownloads/{user_id}.jpg"
    
    # Corrected download method
    await photo_file.download_to_drive(file_path)

    user_states[user_id] = {"step": "waiting_for_utr", "screenshot_path": file_path}
    await update.message.reply_text("ధన్యవాదాలు. ఇప్పుడు మీ UTR నెంబర్ పంపండి.")
