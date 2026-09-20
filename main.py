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

class HealthCheckHandler(BaseHTTPRequestHandler):

    def do_GET(self):
        self.send_response(200)
        self.end_headers()
        self.wfile.write(b"Bot is running!")

    def log_message(self, format, *args):
        pass


def run_web_server():
    port = int(os.environ.get("PORT", "8080"))
    server = HTTPServer(("0.0.0.0", port), HealthCheckHandler)
    server.serve_forever()


# =========================================================
# SETTINGS
# =========================================================

BOT_TOKEN = os.environ.get("BOT_TOKEN")
ADMIN_ID = int(os.environ.get("ADMIN_ID", "0"))
STORAGE_CHAT_ID = int(os.environ.get("STORAGE_CHAT_ID", "0"))

MAIN_CHANNEL = "@House_Of_Anime_Official"
MAIN_CHANNEL_LINK = "https://t.me/House_Of_Anime_Official"


# =========================================================
# FILE DATABASE
# =========================================================
# Example:
# "example": 25
#
# "example" = search name
# 25 = storage chat lo message ID
#
# Actual authorized file message IDs tarvata add cheyyi.
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
# DELETE MESSAGE AFTER 1 HOUR
# =========================================================

async def delete_message_job(context: ContextTypes.DEFAULT_TYPE):

    job = context.job

    try:
        await context.bot.delete_message(
            chat_id=job.data["chat_id"],
            message_id=job.data["message_id"],
        )

        print("Message deleted successfully.")

    except Exception as e:
        print("Delete error:", e)


# =========================================================
# /START
# =========================================================

async def start(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):

    user = update.effective_user
    first_name = user.first_name or "User"

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

    text = (
        f"Hello {first_name}! 👋🏻\n\n"
        "🎬 Welcome to 𝐇𝐎𝐔𝐒𝐄 𝐎𝐅 𝐀𝐍𝐈𝐌𝐄 🫵🏻🌍\n\n"
        "👇🏻 First join our Main Channel.\n\n"
        "After joining, press:\n"
        "✅ I Joined\n\n"
        "Then type the name of the file you want."
    )

    await update.message.reply_text(
        text,
        reply_markup=InlineKeyboardMarkup(keyboard)
    )


# =========================================================
# CHECK CHANNEL MEMBERSHIP
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
                "✅ Membership Verified!\n\n"
                "🎬 Ippudu meeku kavalsina "
                "file name type cheyyandi."
            )

        else:

            await query.message.reply_text(
                "❌ Meeru Main Channel lo join avvaledu.\n\n"
                "First channel lo join avvandi 👇🏻",
                reply_markup=InlineKeyboardMarkup([
                    [
                        InlineKeyboardButton(
                            "🔥 Join Main Channel 🔥",
                            url=MAIN_CHANNEL_LINK
                        )
                    ]
                ])
            )

    except Exception as e:

        print("Join check error:", e)

        await query.message.reply_text(
            "⚠️ Membership check cheyyalekapoyam.\n"
            "Konchem later try cheyyandi."
        )


# =========================================================
# SEARCH FILE
# =========================================================

async def handle_search(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):

    if not update.message:
        return

    user = update.effective_user
    search_text = update.message.text.strip().lower()

    matched_name = None
    matched_message_id = None

    # Search FILES
    for name, message_id in FILES.items():

        if search_text in name.lower():

            matched_name = name
            matched_message_id = message_id

            break

    # =====================================================
    # FILE NOT FOUND
    # =====================================================

    if matched_name is None:

        await update.message.reply_text(
            "✨ FILE NOT FOUND ✨\n\n"
            f"🥺 '{update.message.text}' "
            "store lo dorakaledu.\n\n"
            "Don't Worry! ❤️\n"
            "Mee request admin ki pampincham.\n\n"
            "🔥 Main Channel:\n"
            f"{MAIN_CHANNEL_LINK}",
            disable_web_page_preview=True
        )

        username = (
            f"@{user.username}"
            if user.username
            else "No username"
        )

        try:

            await context.bot.send_message(
                chat_id=ADMIN_ID,
                text=(
                    "⚠️ NEW FILE REQUEST\n\n"
                    f"👤 Name: {user.first_name}\n"
                    f"🔗 Username: {username}\n"
                    f"🆔 User ID: {user.id}\n"
                    f"📁 Requested: {update.message.text}"
                )
            )

        except Exception as e:

            print("Admin alert error:", e)

        return

    # =====================================================
    # CREATE REQUEST
    # =====================================================

    request_id = f"{user.id}_{matched_name}"

    pending_requests[request_id] = {
        "user_id": user.id,
        "file_name": matched_name,
        "message_id": matched_message_id,
    }

    await update.message.reply_text(
        "⏳ Request Admin ki pampincham.\n\n"
        "Admin approve chesina tarvata "
        "file ikkada pampabadutundi. 🔥"
    )

    # =====================================================
    # ADMIN BUTTONS
    # =====================================================

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

    username = (
        f"@{user.username}"
        if user.username
        else "No username"
    )

    try:

        await context.bot.send_message(
            chat_id=ADMIN_ID,
            text=(
                "🔔 NEW REQUEST\n\n"
                f"👤 User: {user.first_name}\n"
                f"🔗 Username: {username}\n"
                f"🆔 User ID: {user.id}\n\n"
                f"📁 Requested: {matched_name}"
            ),
            reply_markup=InlineKeyboardMarkup(keyboard)
        )

    except Exception as e:

        print("Admin request error:", e)


# =========================================================
# ADMIN APPROVE / REJECT
# =========================================================

async def admin_action(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):

    query = update.callback_query

    # Only ADMIN can use buttons
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

    # Check request
    if request_id not in pending_requests:

        await query.edit_message_text(
            "⚠️ This request was already processed."
        )

        return

    request = pending_requests.pop(request_id)

    user_id = request["user_id"]
    file_name = request["file_name"]
    message_id = request["message_id"]

    # =====================================================
    # APPROVE
    # =====================================================

    if action == "app":

        try:

            # Copy file from storage to user
            sent = await context.bot.copy_message(
                chat_id=user_id,
                from_chat_id=STORAGE_CHAT_ID,
                message_id=message_id,
                protect_content=True
            )

            # Delete copied file after 1 hour
            context.job_queue.run_once(
                delete_message_job,
                when=3600,
                data={
                    "chat_id": user_id,
                    "message_id": sent.message_id
                }
            )

            # Approval message
            approval_message = await context.bot.send_message(
                chat_id=user_id,
                text=(
                    "🎉 REQUEST APPROVED! 🎉\n\n"
                    f"📁 {file_name}\n\n"
                    "⚠️ Ee file 1 hour tarvata "
                    "auto-delete avutundi.\n\n"
                    "🔒 Forwarding/Saving restricted."
                )
            )

            # Delete approval message after 1 hour
            context.job_queue.run_once(
                delete_message_job,
                when=3600,
                data={
                    "chat_id": user_id,
                    "message_id": approval_message.message_id
                }
            )

            await query.edit_message_text(
                "✅ APPROVED\n\n"
                f"📁 {file_name}\n"
                f"👤 User ID: {user_id}\n\n"
                "📤 File sent successfully."
            )

        except Exception as e:

            print("Send error:", e)

            await query.edit_message_text(
                "❌ File send avvaledu.\n\n"
                "Storage chat / message ID / "
                "bot access check cheyyandi."
            )

    # =====================================================
    # REJECT
    # =====================================================

    elif action == "rej":

        try:

            await context.bot.send_message(
                chat_id=user_id,
                text=(
                    "❌ Request Rejected.\n\n"
                    f"📁 {file_name}\n\n"
                    "Admin request approve cheyyaledu."
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
# ERROR HANDLER
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

    if ADMIN_ID == 0:
        print("❌ ADMIN_ID missing")
        return

    if STORAGE_CHAT_ID == 0:
        print("❌ STORAGE_CHAT_ID missing")
        return

    # Render health server
    threading.Thread(
        target=run_web_server,
        daemon=True
    ).start()

    # Telegram application
    application = (
        Application.builder()
        .token(BOT_TOKEN)
        .build()
    )

    # /start
    application.add_handler(
        CommandHandler("start", start)
    )

    # Join check
    application.add_handler(
        CallbackQueryHandler(
            check_join,
            pattern="^check_join$"
        )
    )

    # Admin approve/reject
    application.add_handler(
        CallbackQueryHandler(
            admin_action,
            pattern="^(app|rej)_"
        )
    )

    # File search
    application.add_handler(
        MessageHandler(
            filters.TEXT & ~filters.COMMAND,
            handle_search
        )
    )

    # Error handler
    application.add_error_handler(
        error_handler
    )

    print("🔥 HOUSE OF ANIME BOT STARTED!")

    application.run_polling()


# =========================================================
# START PROGRAM
# =========================================================

if __name__ == "__main__":
    main()
