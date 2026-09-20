import asyncio
from pyrogram import Client, filters
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton

API_ID = 30663433
API_HASH = "65cc6e1125b0b08ce45cd8e54d1fcda0"
BOT_TOKEN = "8809605820:AAFs8BJ-tBYVGF6vv97Q4ZuNMC1Tef0xs4E"
CHANNEL_ID = -1003618758770
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

if __name__ == "__main__":
    try:
        asyncio.get_event_loop()
    except RuntimeError:
        asyncio.set_event_loop(asyncio.new_event_loop())
    app.run()
