import os
import threading
from http.server import HTTPServer, BaseHTTPRequestHandler
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, ContextTypes

# --- Web Server for Render Keep-Alive ---
class HealthCheckHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.end_headers()
        self.wfile.write(b"Bot is Running Alive!")

def run_web_server():
    port = int(os.environ.get("PORT", 8080))
    server = HTTPServer(('0.0.0.0', port), HealthCheckHandler)
    server.serve_forever()

# --- Telegram Bot Handler ---
BOT_TOKEN = "8809605820:AAFs8BJ-tBYVGF6vv97Q4ZuNMC1Tef0xs4E"
FORCE_JOIN_LINK = "https://t.me/Madara_217"

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [[InlineKeyboardButton("🔥 Join Main Group 🔥", url=FORCE_JOIN_LINK)]]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text(
        f"Hello {update.effective_user.first_name}!\n\n"
        f"Welcome to 𝐇𝐎𝐔𝐒𝐄 𝐎𝐅 𝐀𝐍𝐈𝐌𝐄 🫵🏻🌍\n\n"
        f"Anime files mariyu access pondadaaniki, main group lo join avvandi!",
        reply_markup=reply_markup
    )

def main():
    # Background thread lo HTTP Web Server start avuthundhi
    threading.Thread(target=run_web_server, daemon=True).start()
    
    # Telegram Bot Polling
    app = Application.builder().token(BOT_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    print("Bot is starting...")
    app.run_polling()

if __name__ == "__main__":
    main()
    # Telegram Bot Polling
    app = Application.builder().token(BOT_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    print("Bot is starting...")
    app.run_polling()

if __name__ == "__main__":
    main()
