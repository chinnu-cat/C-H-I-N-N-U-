import asyncio
from flask import Flask
from threading import Thread
from pyrogram import Client, filters, idle
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton

# Dummy Web Server for Render Web Service Keep-Alive
web_app = Flask('')

@web_app.route('/')
def home():
    return "Bot is Alive!"

def run_web():
    web_app.run(host='0.0.0.0', port=8080)

def keep_alive():
    t = Thread(target=run_web)
    t.start()

# Bot Configuration
API_ID = 30663433
API_HASH = "65cc6e1125b0b08ce45cd8e54d1fcda0"
BOT_TOKEN = "8809605820:AAFs8BJ-tBYVGF6vv97Q4ZuNMC1Tef0xs4E"
FORCE_JOIN_LINK = "https://t.me/Madara_217"

app = Client("chinnubot", api_id=API_ID, api_hash=API_HASH, bot_token=BOT_TOKEN)

@app.on_message(filters.command("start") & filters.private)
async def start_cmd(client, message):
    buttons = InlineKeyboardMarkup([
        [InlineKeyboardButton("🔥 Join Main Group 🔥", url=FORCE_JOIN_LINK)]
    ])
    await message.reply_text(
        f"Hello {message.from_user.first_name}!\n\nWelcome to Chinnu Anime Bot.\n"
        f"Anime files mariyu search access pondadaaniki, mundhu ga mana main group lo join avvandi!",
        reply_markup=buttons
    )

async def main():
    keep_alive()  # Start Dummy Web Server
    await app.start()
    print("Bot Live Ayyindhi!")
    await idle()
    await app.stop()

if __name__ == "__main__":
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    loop.run_until_complete(main())
