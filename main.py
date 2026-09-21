import os
import threading
from http.server import HTTPServer, BaseHTTPRequestHandler

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    CallbackQueryHandler,
    ContextTypes,
    filters,
)


# =========================================================
# RENDER HEALTH CHECK
# =========================================================

class HealthHandler(BaseHTTPRequestHandler):

    def do_GET(self):
        self.send_response(200)
        self.end_headers()
        self.wfile.write(b"Bot is running!")

    def log_message(self, format, *args):
        pass


def run_server():
    port = int(os.environ.get("PORT", "8080"))
    server = HTTPServer(("0.0.0.0", port), HealthHandler)
    server.serve_forever()


# =========================================================
# SETTINGS
# =========================================================

BOT_TOKEN = os.environ.get("BOT_TOKEN")
ADMIN_ID = int(os.environ.get("ADMIN_ID", "0"))
STORAGE_CHAT_ID = int(os.environ.get("STORAGE_CHAT_ID", "0"))

MAIN_CHANNEL = "@madara_217"
MAIN_CHANNEL_LINK = "https://t.me/madara_217"


# =========================================================
# FILES
# =========================================================

FILES = {
    "example": 25,
    "sample": 30,
}


# =========================================================
# PENDING REQUESTS
# =========================================================

pending_requests = {}


# =========================================================
# DELETE AFTER 1 HOUR
# =========================================================

async def delete_message(context: ContextTypes.DEFAULT_TYPE):

    data = context.job.data

    try:
        await context.bot.delete_message(
            chat_id=data["chat_id"],
            message_id=data["message_id"]
        )
    except Exception as e:
        print("Delete error:", e)


# =========================================================
# START
# =========================================================

async def start(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):

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
                callback_data="check_join"
            )
        ]
    ]

    await update.message.reply_text(
        "🎬 Welcome to HOUSE OF ANIME 🫵🏻🌍\n\n"
        "🔥 Search your favourite anime\n"
        "📥 Request your files\n"
        "⏳ Admin approval required\n\n"
        "👇🏻 First join our Main Channel.",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )


# =========================================================
# CHECK JOIN
# =========================================================

async def check_join(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):

    query = update.callback_query
    await query.answer()

    user_id = query.from_user.id

    try:

        member = await context.bot.get_chat_member(
            chat_id=MAIN_CHANNEL,
            user_id=user_id
        )

        if member.status in (
            "member",
            "administrator",
            "creator"
        ):

            await query.message.reply_text(
                "✅ Joined successfully!\n\n"
                "📥 Ippudu meeku kavalsina "
                "file name type cheyyandi."
            )

        else:

            await query.message.reply_text(
                "❌ First Main Channel lo join avvandi.",
                reply_markup=InlineKeyboardMarkup([
                    [
                        InlineKeyboardButton(
                            "🔥 Join Channel 🔥",
                            url=MAIN_CHANNEL_LINK
                        )
                    ]
                ])
            )

    except Exception as e:

        print("Join check error:", e)

        await query.message.reply_text(
            "⚠️ Membership check failed.\n"
            "Please try again."
        )


# =========================================================
# SEARCH
# =========================================================

async def search_file(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):

    if not update.message:
        return

    user = update.effective_user
    search = update.message.text.strip().lower()

    matched_name = None
    matched_message_id = None

    for name, message_id in FILES.items():

        if search in name.lower():

            matched_name = name
            matched_message_id = message_id
            break

    # FILE NOT FOUND
    if matched_name is None:

        await update.message.reply_text(
            "❌ FILE NOT FOUND\n\n"
            f"📁 {update.message.text}\n\n"
            "Your request has been sent to Admin."
        )

        try:

            await context.bot.send_message(
                chat_id=ADMIN_ID,
                text=(
                    "🔔 NEW REQUEST\n\n"
                    f"👤 User: {user.first_name}\n"
                    f"🆔 User ID: {user.id}\n"
                    f"📁 Request: {update.message.text}"
                )
            )

        except Exception as e:

            print("Admin alert error:", e)

        return

    # REQUEST ID
    request_id = f"{user.id}_{matched_name}"

    pending_requests[request_id] = {
        "user_id": user.id,
        "file_name": matched_name,
        "message_id": matched_message_id
    }

    await update.message.reply_text(
        "⏳ Request Admin ki pampincham.\n\n"
        "Admin approve chesina tarvata file "
        "ikkada send avutundi."
    )

    # ADMIN BUTTONS
    keyboard = [
        [
            InlineKeyboardButton(
                "✅ Approve & Send",
                callback_data=f"app_{request_id}"
            ),
            InlineKeyboardButton(
                "❌ Reject",
                callback_data=f"rej_{request_id}"
            )
        ]
    ]

    try:

        await context.bot.send_message(
            chat_id=ADMIN_ID,
            text=(
                "🔔 NEW FILE REQUEST\n\n"
                f"👤 User: {user.first_name}\n"
                f"🆔 User ID: {user.id}\n"
                f"📁 File: {matched_name}"
            ),
            reply_markup=InlineKeyboardMarkup(keyboard)
        )

    except Exception as e:

        print("Admin request error:", e)


# =========================================================
# ADMIN ACTION
# =========================================================

async def admin_action(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):

    query = update.callback_query

    if query.from_user.id != ADMIN_ID:

        await query.answer(
            "❌ Not authorized.",
            show_alert=True
        )
        return

    await query.answer()

    try:

        action, request_id = query.data.split("_", 1)

    except ValueError:

        await query.edit_message_text(
            "❌ Invalid request."
        )
        return

    if request_id not in pending_requests:

        await query.edit_message_text(
            "⚠️ Request already processed."
        )
        return

    request = pending_requests.pop(request_id)

    user_id = request["user_id"]
    file_name = request["file_name"]
    message_id = request["message_id"]

    # APPROVE
    if action == "app":

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
                when=3600,
                data={
                    "chat_id": user_id,
                    "message_id": sent.message_id
                }
            )

            info = await context.bot.send_message(
                chat_id=user_id,
                text=(
                    "🎉 REQUEST APPROVED!\n\n"
                    f"📁 {file_name}\n\n"
                    "⏳ This file will be deleted "
                    "after 1 hour."
                )
            )

            # Delete info message after 1 hour
            context.job_queue.run_once(
                delete_message,
                when=3600,
                data={
                    "chat_id": user_id,
                    "message_id": info.message_id
                }
            )

            await query.edit_message_text(
                "✅ APPROVED\n\n"
                f"📁 {file_name}\n"
                f"👤 User ID: {user_id}\n\n"
                "📤 File sent."
            )

        except Exception as e:

            print("Send error:", e)

            await query.edit_message_text(
                "❌ File send failed.\n\n"
                "Check STORAGE_CHAT_ID and message ID."
            )

    # REJECT
    elif action == "rej":

        try:

            await context.bot.send_message(
                chat_id=user_id,
                text=(
                    "❌ Request Rejected.\n\n"
                    f"📁 {file_name}"
                )
            )

        except Exception as e:

            print("Reject notification error:", e)

        await query.edit_message_text(
            "❌ REJECTED\n\n"
            f"📁 {file_name}\n"
            f"👤 User ID: {user_id}"
        )


# =========================================================
# ERROR
# =========================================================

async def error_handler(
    update: object,
    context: ContextTypes.DEFAULT_TYPE
):

    print("BOT ERROR:", context.error)


# =========================================================
# MAIN
# =========================================================

def main():

    if not BOT_TOKEN:
        print("❌ BOT_TOKEN missing")
        return

    threading.Thread(
        target=run_server,
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
            pattern="^check_join$"
        )
    )

    app.add_handler(
        CallbackQueryHandler(
            admin_action,
            pattern="^(app|rej)_"
        )
    )

    app.add_handler(
        MessageHandler(
            filters.TEXT & ~filters.COMMAND,
            search_file
        )
    )

    app.add_error_handler(error_handler)

    print("🔥 HOUSE OF ANIME BOT STARTED!")

    app.run_polling()


if __name__ == "__main__":
    main()
