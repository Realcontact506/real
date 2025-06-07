from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters, ContextTypes
from PIL import Image
import io
import torch
from realesrgan import RealESRGAN

TOKEN = '8118983802:AAG8ULPLB_6LIJqRAbyoiqXq17nc6YAlghc'

device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
model = RealESRGAN(device, scale=4)
model.load_weights('weights/RealESRGAN_x4.pth')

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Hi! Send me a photo, I will enhance it with AI.")

async def enhance_photo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    photo_file = await update.message.photo[-1].get_file()
    photo_bytes = await photo_file.download_as_bytearray()

    input_image = Image.open(io.BytesIO(photo_bytes)).convert('RGB')
    output_image = model.predict(input_image)

    bio = io.BytesIO()
    bio.name = 'enhanced.png'
    output_image.save(bio, 'PNG')
    bio.seek(0)

    await update.message.reply_photo(photo=bio, caption="AI enhanced photo ready!")

def main():
    app = ApplicationBuilder().token(TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.PHOTO, enhance_photo))

    print("Bot is running...")
    app.run_polling()

main()
