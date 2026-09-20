import os
import asyncio
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, ContextTypes

BOT_TOKEN = "8809605820:AAFs8BJ-tBYVGF6vv97Q4ZuNMC1Tef0xs4E"
FORCE_JOIN_LINK = "https://t.me/Madara_217"

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [[InlineKeyboardButton("🔥 Join Main Group 🔥", url=FORCE_JOIN_LINK)]]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text(
        f"Hello {update.effective_user.first_name}!\n\n"
        f"Welcome to Chinnu Anime Bot.\n"
        f"Anime files mariyu access pondadaaniki, main group lo join avvandi!",
        reply_markup=reply_markup
    )

def main():
    # Render Port Binding Fix
    port = int(os.environ.get("PORT", 8080))
    app = Application.builder().token(BOT_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    
    print(f"Bot running on port {port}...")
    app.run_polling()

if __name__ == "__main__":
    main()
if __name__ == "__main__":
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    loop.run_until_complete(main())
