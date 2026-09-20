import os
import threading
from http.server import BaseHTTPRequestHandler, HTTPServer

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    CallbackQueryHandler,
    ContextTypes,
    filters,
)


# =========================
# SETTINGS
# =========================

BOT_TOKEN = os.getenv("BOT_TOKEN")
ADMIN_ID = int(os.getenv("ADMIN_ID", "0"))
STORAGE_CHAT_ID = int(os.getenv("STORAGE_CHAT_ID", "0"))

MAIN_CHANNEL = "@House_Of_Anime_Official"
MAIN_CHANNEL_LINK = "https://t.me/House_Of_Anime_Official"


# =========================
# FILE DATABASE
# =========================
# Example only.
# Replace these later with your own/authorized storage message IDs.

FILES = {
    "example": 25,
    "sample": 30,
}


pending = {}


# =========================
# RENDER HEALTH CHECK
# =========================

class HealthHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.end_headers()
        self.wfile.write(b"Bot is running")

    def log_message(self, *args):
        pass


def start_web_server():
    port = int(os.getenv("PORT", "8080"))
    server = HTTPServer(("0.0.0.0", port), HealthHandler)
    server.serve_forever()


# =========================
# START
# =========================

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):

    keyboard = [
        [
            InlineKeyboardButton(
                "🔥 Join Main Channel 🔥",
                url=MAIN_CHANNEL_LINK
            )
        ],
        [
            InlineKeyboardButton(
                "✅ I Joined",
                callback_data="joined"
            )
        ]
    ]

    await update.message.reply_text(
        "🎬 Welcome to HOUSE OF ANIME 🫵🏻🌍\n\n"
        "🔥 First join our Main Channel.\n\n"
        "After joining, press ✅ I Joined.",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )


# =========================
# CHECK JOIN
# =========================

async def check_join(update: Update, context: ContextTypes.DEFAULT_TYPE):

    query = update.callback_query
    await query.answer()

    try:
        member = await context.bot.get_chat_member(
            chat_id=MAIN_CHANNEL,
            user_id=query.from_user.id
        )

        if member.status in ("member", "administrator", "creator"):

            await query.message.reply_text(
                "✅ Joined successfully!\n\n"
                "📁 Ippudu kavalsina file name type cheyyandi."
            )

        else:

            await query.message.reply_text(
                "❌ First Main Channel lo join avvandi."
            )

    except Exception as e:

        print("Join check error:", e)

        await query.message.reply_text(
            "⚠️ Join check failed.\n"
            "Konchem later try cheyyandi."
        )


# =========================
# SEARCH
# =========================

async def search_file(update: Update, context: ContextTypes.DEFAULT_TYPE):

    text = update.message.text.strip().lower()

    found_name = None
    found_message_id = None

    for name, message_id in FILES.items():

        if text in name.lower():
            found_name = name
            found_message_id = message_id
            break

    # FILE NOT FOUND
    if not found_name:

        await update.message.reply_text(
            "❌ FILE NOT FOUND\n\n"
            f"📁 Requested: {update.message.text}\n\n"
            "Your request has been sent to Admin. ⏳"
        )

        try:
            await context.bot.send_message(
                chat_id=ADMIN_ID,
                text=(
                    "🔔 NEW FILE REQUEST\n\n"
                    f"👤 User: {update.effective_user.first_name}\n"
                    f"🆔 User ID: {update.effective_user.id}\n"
                    f"📁 Request: {update.message.text}"
                )
            )
        except Exception as e:
            print("Admin alert error:", e)

        return

    # SAVE REQUEST
    request_id = f"{update.effective_user.id}:{found_name}"

    pending[request_id] = {
        "user_id": update.effective_user.id,
        "file_name": found_name,
        "message_id": found_message_id
    }

    keyboard = [
        [
            InlineKeyboardButton(
                "✅ Approve & Send",
                callback_data=f"approve:{request_id}"
            ),
            InlineKeyboardButton(
                "❌ Reject",
                callback_data=f"reject:{request_id}"
            )
        ]
    ]

    await update.message.reply_text(
        "⏳ Request Admin ki pampincham.\n"
        "Approval tarvata file send avutundi."
    )

    await context.bot.send_message(
        chat_id=ADMIN_ID,
        text=(
            "🔔 NEW REQUEST\n\n"
            f"👤 User: {update.effective_user.first_name}\n"
            f"🆔 User ID: {update.effective_user.id}\n"
            f"📁 File: {found_name}"
        ),
        reply_markup=InlineKeyboardMarkup(keyboard)
    )


# =========================
# ADMIN ACTION
# =========================

async def admin_action(update: Update, context: ContextTypes.DEFAULT_TYPE):

    query = update.callback_query
    await query.answer()

    if query.from_user.id != ADMIN_ID:
        await query.answer(
            "❌ Not authorized.",
            show_alert=True
        )
        return

    action, request_id = query.data.split(":", 1)

    request = pending.pop(request_id, None)

    if not request:
        await query.edit_message_text(
            "⚠️ Request already processed."
        )
        return

    user_id = request["user_id"]
    file_name = request["file_name"]
    message_id = request["message_id"]

    # REJECT
    if action == "reject":

        await context.bot.send_message(
            chat_id=user_id,
            text=(
                "❌ Request Rejected.\n\n"
                f"📁 {file_name}"
            )
        )

        await query.edit_message_text(
            f"❌ Rejected\n\n📁 {file_name}"
        )

        return

    # APPROVE
    try:

        sent = await context.bot.copy_message(
            chat_id=user_id,
            from_chat_id=STORAGE_CHAT_ID,
            message_id=message_id,
            protect_content=True
        )

        # Delete file after 1 hour
        context.job_queue.run_once(
            delete_message,
            3600,
            data={
                "chat_id": user_id,
                "message_id": sent.message_id
            }
        )

        info = await context.bot.send_message(
            chat_id=user_id,
            text=(
                "✅ Request Approved!\n\n"
                f"📁 {file_name}\n\n"
                "⏳ This file will be deleted after 1 hour."
            )
        )

        # Delete info message after 1 hour
        context.job_queue.run_once(
            delete_message,
            3600,
            data={
                "chat_id": user_id,
                "message_id": info.message_id
            }
        )

        await query.edit_message_text(
            f"✅ Sent successfully\n\n"
            f"📁 {file_name}\n"
            f"🆔 User ID: {user_id}"
        )

    except Exception as e:

        print("File send error:", e)

        await query.edit_message_text(
            "❌ File send failed.\n\n"
            "Check STORAGE_CHAT_ID and message ID."
        )


# =========================
# DELETE
# =========================

async def delete_message(context: ContextTypes.DEFAULT_TYPE):

    data = context.job.data

    try:
        await context.bot.delete_message(
            chat_id=data["chat_id"],
            message_id=data["message_id"]
        )

    except Exception as e:
        print("Delete error:", e)


# =========================
# ERROR
# =========================

async def error_handler(update, context):

    print("ERROR:", context.error)


# =========================
# MAIN
# =========================

def main():

    if not BOT_TOKEN:
        print("BOT_TOKEN missing")
        return

    threading.Thread(
        target=start_web_server,
        daemon=True
    ).start()

    app = (
        Application.builder()
        .token(BOT_TOKEN)
        .build()
    )

    app.add_handler(
        CommandHandler("start", start)
    )

    app.add_handler(
        CallbackQueryHandler(
            check_join,
            pattern="^joined$"
        )
    )

    app.add_handler(
        CallbackQueryHandler(
            admin_action,
            pattern="^(approve|reject):"
        )
    )

    app.add_handler(
        MessageHandler(
            filters.TEXT & ~filters.COMMAND,
            search_file
        )
    )

    app.add_error_handler(error_handler)

    print("HOUSE OF ANIME BOT STARTED")

    app.run_polling()


# =========================
# RUN
# =========================

if __name__ == "__main__":
    main()
