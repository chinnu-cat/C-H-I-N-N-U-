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

# =====================================================
# SETTINGS
# =====================================================

BOT_TOKEN = os.getenv("BOT_TOKEN")
ADMIN_ID = int(os.getenv("ADMIN_ID", "0"))
STORAGE_CHAT_ID = int(os.getenv("STORAGE_CHAT_ID", "0"))

CHANNEL = "@House_Of_Anime_Official"
CHANNEL_LINK = "https://t.me/House_Of_Anime_Official"


# =====================================================
# FILE DATABASE
# =====================================================
# Example:
# "example": 123
#
# example = search name
# 123 = private storage channel message ID
#
# Nee authorized files message IDs ikkada add cheyyali.
# =====================================================

FILES = {
    "example": 123,
}


# =====================================================
# RENDER HEALTH CHECK
# =====================================================

class Health(BaseHTTPRequestHandler):

    def do_GET(self):
        self.send_response(200)
        self.end_headers()
        self.wfile.write(b"Bot is running")

    def log_message(self, *args):
        pass


def health_server():
    port = int(os.getenv("PORT", "10000"))
    server = HTTPServer(("0.0.0.0", port), Health)
    server.serve_forever()


# =====================================================
# DELETE FILE AFTER 1 HOUR
# =====================================================

async def delete_after_one_hour(context: ContextTypes.DEFAULT_TYPE):

    data = context.job.data

    try:
        await context.bot.delete_message(
            chat_id=data["chat_id"],
            message_id=data["message_id"]
        )
        print("Deleted after 1 hour")

    except Exception as e:
        print("Delete error:", e)


# =====================================================
# START
# =====================================================

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):

    buttons = [
        [
            InlineKeyboardButton(
                "🔥 Join Main Channel",
                url=CHANNEL_LINK
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
        "🎬 HOUSE OF ANIME 🫵🏻🌍\n\n"
        "🔥 First join our Main Channel.\n\n"
        "After joining, press:\n"
        "✅ I Joined\n\n"
        "Then send the file name.",
        reply_markup=InlineKeyboardMarkup(buttons)
    )


# =====================================================
# CHECK JOIN
# =====================================================

async def check_join(update: Update, context: ContextTypes.DEFAULT_TYPE):

    query = update.callback_query
    await query.answer()

    user_id = query.from_user.id

    try:

        member = await context.bot.get_chat_member(
            chat_id=CHANNEL,
            user_id=user_id
        )

        if member.status in ["member", "administrator", "creator"]:

            await query.message.reply_text(
                "✅ Joined successfully!\n\n"
                "📁 Ippudu meeku kavalsina "
                "file name pampinchandi."
            )

        else:

            await query.message.reply_text(
                "❌ First Main Channel lo join avvandi.",
                reply_markup=InlineKeyboardMarkup([
                    [
                        InlineKeyboardButton(
                            "🔥 Join Channel",
                            url=CHANNEL_LINK
                        )
                    ]
                ])
            )

    except Exception as e:

        print("Join check error:", e)

        await query.message.reply_text(
            "⚠️ Join check failed.\n"
            "Please try again."
        )


# =====================================================
# SEARCH
# =====================================================

async def search_file(update: Update, context: ContextTypes.DEFAULT_TYPE):

    text = update.message.text.strip().lower()

    found_name = None
    found_message_id = None

    for name, message_id in FILES.items():

        if text in name.lower():

            found_name = name
            found_message_id = message_id
            break

    # -------------------------------------------------
    # NOT FOUND
    # -------------------------------------------------

    if found_name is None:

        await update.message.reply_text(
            "❌ FILE NOT FOUND\n\n"
            f"🔎 Search: {update.message.text}\n\n"
            "📩 Your request has been sent to Admin."
        )

        try:

            await context.bot.send_message(
                chat_id=ADMIN_ID,
                text=(
                    "🔔 NEW FILE REQUEST\n\n"
                    f"👤 User: {update.effective_user.first_name}\n"
                    f"🆔 ID: {update.effective_user.id}\n"
                    f"📁 Request: {update.message.text}"
                )
            )

        except Exception as e:

            print("Admin notification error:", e)

        return

    # -------------------------------------------------
    # SEND REQUEST TO ADMIN
    # -------------------------------------------------

    request_id = (
        f"{update.effective_user.id}|"
        f"{found_name}"
    )

    pending[request_id] = {
        "user_id": update.effective_user.id,
        "message_id": found_message_id,
        "name": found_name
    }

    buttons = [
        [
            InlineKeyboardButton(
                "✅ APPROVE",
                callback_data=f"approve|{request_id}"
            ),
            InlineKeyboardButton(
                "❌ REJECT",
                callback_data=f"reject|{request_id}"
            )
        ]
    ]

    await update.message.reply_text(
        "⏳ Request Admin ki pampincham.\n\n"
        "✅ Admin approve chesina tarvata "
        "file meeku send avutundi."
    )

    try:

        await context.bot.send_message(
            chat_id=ADMIN_ID,
            text=(
                "🔔 NEW FILE REQUEST\n\n"
                f"👤 User: {update.effective_user.first_name}\n"
                f"🆔 ID: {update.effective_user.id}\n"
                f"📁 File: {found_name}"
            ),
            reply_markup=InlineKeyboardMarkup(buttons)
        )

    except Exception as e:

        print("Admin request error:", e)


# =====================================================
# PENDING REQUESTS
# =====================================================

pending = {}


# =====================================================
# ADMIN APPROVE / REJECT
# =====================================================

async def admin_action(update: Update, context: ContextTypes.DEFAULT_TYPE):

    query = update.callback_query

    if query.from_user.id != ADMIN_ID:

        await query.answer(
            "❌ Not allowed",
            show_alert=True
        )
        return

    await query.answer()

    try:

        action, request_id = query.data.split("|", 1)

    except Exception:

        await query.edit_message_text(
            "❌ Invalid request."
        )
        return

    request = pending.pop(request_id, None)

    if not request:

        await query.edit_message_text(
            "⚠️ Request already processed."
        )
        return

    user_id = request["user_id"]
    message_id = request["message_id"]
    name = request["name"]

    # =================================================
    # APPROVE
    # =================================================

    if action == "approve":

        try:

            sent = await context.bot.copy_message(
                chat_id=user_id,
                from_chat_id=STORAGE_CHAT_ID,
                message_id=message_id,
                protect_content=True
            )

            context.job_queue.run_once(
                delete_after_one_hour,
                3600,
                data={
                    "chat_id": user_id,
                    "message_id": sent.message_id
                }
            )

            await context.bot.send_message(
                chat_id=user_id,
                text=(
                    "✅ REQUEST APPROVED\n\n"
                    f"📁 {name}\n\n"
                    "⏳ File 1 hour tarvata "
                    "auto-delete avutundi."
                )
            )

            await query.edit_message_text(
                "✅ APPROVED\n\n"
                f"📁 {name}\n"
                f"👤 User ID: {user_id}\n\n"
                "📤 File sent."
            )

        except Exception as e:

            print("Send error:", e)

            await query.edit_message_text(
                "❌ File send failed.\n\n"
                "Storage chat/message ID check cheyyandi."
            )

    # =================================================
    # REJECT
    # =================================================

    elif action == "reject":

        try:

            await context.bot.send_message(
                chat_id=user_id,
                text=(
                    "❌ REQUEST REJECTED\n\n"
                    f"📁 {name}"
                )
            )

        except Exception as e:

            print("Reject message error:", e)

        await query.edit_message_text(
            "❌ REJECTED\n\n"
            f"📁 {name}\n"
            f"👤 User ID: {user_id}"
        )


# =====================================================
# MAIN
# =====================================================

def main():

    if not BOT_TOKEN:
        print("❌ BOT_TOKEN missing")
        return

    threading.Thread(
        target=health_server,
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
            pattern="^(approve|reject)\\|"
        )
    )

    app.add_handler(
        MessageHandler(
            filters.TEXT & ~filters.COMMAND,
            search_file
        )
    )

    print("🔥 HOUSE OF ANIME BOT STARTED")

    app.run_polling()


# =====================================================
# START BOT
# =====================================================

if __name__ == "__main__":
    main()# Actual authorized storage message IDs later add cheyyali.
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
# RENDER HEALTH CHECK
# =========================================================

class HealthHandler(BaseHTTPRequestHandler):

    def do_GET(self):
        self.send_response(200)
        self.end_headers()
        self.wfile.write(b"Bot is running!")

    def log_message(self, format, *args):
        pass


def start_health_server():
    port = int(os.environ.get("PORT", "8080"))
    server = HTTPServer(("0.0.0.0", port), HealthHandler)
    server.serve_forever()


# =========================================================
# AUTO DELETE
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
        "🎬 Welcome to 𝐇𝐎𝐔𝐒𝐄 𝐎𝐅 𝐀𝐍𝐈𝐌𝐄 🫵🏻🌍\n\n"
        "🔥 Search • Request • Download\n\n"
        "👇🏻 First join our Main Channel.\n\n"
        "After joining press:\n"
        "✅ I Joined",
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
                "✅ Join Verified!\n\n"
                "🎬 Ippudu meeku kavalsina "
                "file name type cheyyandi."
            )

        else:

            await query.message.reply_text(
                "❌ Meeru Main Channel lo join avvaledu.\n\n"
                "First join avvandi 👇🏻",
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
            "⚠️ Join check cheyyalekapoyam.\n"
            "Konchem later try cheyyandi."
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

    text = update.message.text.strip().lower()

    matched_name = None
    matched_message_id = None

    for name, message_id in FILES.items():

        if text in name.lower():

            matched_name = name
            matched_message_id = message_id
            break

    # -----------------------------------------------------
    # NOT FOUND
    # -----------------------------------------------------

    if matched_name is None:

        await update.message.reply_text(
            "✨ FILE NOT FOUND ✨\n\n"
            f"🥺 '{update.message.text}' store lo dorakaledu.\n\n"
            "Mee request admin ki pampincham. ❤️"
        )

        try:

            await context.bot.send_message(
                chat_id=ADMIN_ID,
                text=(
                    "⚠️ NEW FILE REQUEST\n\n"
                    f"👤 User: {update.effective_user.first_name}\n"
                    f"🆔 User ID: {update.effective_user.id}\n"
                    f"📁 Requested: {update.message.text}"
                )
            )

        except Exception as e:
            print("Admin alert error:", e)

        return

    # -----------------------------------------------------
    # SAVE REQUEST
    # -----------------------------------------------------

    request_id = (
        f"{update.effective_user.id}_{matched_name}"
    )

    pending_requests[request_id] = {
        "user_id": update.effective_user.id,
        "file_name": matched_name,
        "message_id": matched_message_id
    }

    await update.message.reply_text(
        "⏳ Request admin ki pampincham.\n\n"
        "Admin approve chesina tarvata "
        "file ikkada pampabadutundi. 🔥"
    )

    # -----------------------------------------------------
    # ADMIN BUTTONS
    # -----------------------------------------------------

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

    try:

        await context.bot.send_message(
            chat_id=ADMIN_ID,
            text=(
                "🔔 NEW REQUEST\n\n"
                f"👤 User: {update.effective_user.first_name}\n"
                f"🆔 User ID: {update.effective_user.id}\n"
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

    # Only admin
    if query.from_user.id != ADMIN_ID:

        await query.answer(
            "❌ Not authorized.",
            show_alert=True
        )

        return

    await query.answer()

    try:

        action, request_id = query.data.split(":", 1)

    except Exception:

        await query.edit_message_text(
            "❌ Invalid request."
        )

        return

    # Request exists?
    if request_id not in pending_requests:

        await query.edit_message_text(
            "⚠️ Request already processed."
        )

        return

    request = pending_requests.pop(request_id)

    user_id = request["user_id"]
    file_name = request["file_name"]
    message_id = request["message_id"]

    # =====================================================
    # APPROVE
    # =====================================================

    if action == "approve":

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
                    "🎉 REQUEST APPROVED! 🎉\n\n"
                    f"📁 {file_name}\n\n"
                    "⏳ Ee file 1 hour tarvata "
                    "auto-delete avutundi."
                )
            )

            # Delete info after 1 hour
            context.job_queue.run_once(
                delete_message,
                3600,
                data={
                    "chat_id": user_id,
                    "message_id": info.message_id
                }
            )

            await query.edit_message_text(
                "✅ APPROVED\n\n"
                f"📁 {file_name}\n"
                f"🆔 User ID: {user_id}\n\n"
                "📤 File sent successfully."
            )

        except Exception as e:

            print("Send error:", e)

            await query.edit_message_text(
                "❌ File send avvaledu.\n\n"
                "Storage chat/message ID "
                "check cheyyandi."
            )

    # =====================================================
    # REJECT
    # =====================================================

    elif action == "reject":

        try:

            await context.bot.send_message(
                chat_id=user_id,
                text=(
                    "❌ Request Rejected.\n\n"
                    f"📁 {file_name}"
                )
            )

        except Exception as e:
            print("Reject error:", e)

        await query.edit_message_text(
            "❌ REJECTED\n\n"
            f"📁 {file_name}\n"
            f"🆔 User ID: {user_id}"
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

    # Render server
    threading.Thread(
        target=start_health_server,
        daemon=True
    ).start()

    # Telegram bot
    app = (
        Application.builder()
        .token(BOT_TOKEN)
        .build()
    )

    # Commands
    app.add_handler(
        CommandHandler("start", start)
    )

    # Join button
    app.add_handler(
        CallbackQueryHandler(
            check_join,
            pattern=r"^check_join$"
        )
    )

    # Admin buttons
    app.add_handler(
        CallbackQueryHandler(
            admin_action,
            pattern=r"^(approve|reject):"
        )
    )

    # Search text
    app.add_handler(
        MessageHandler(
            filters.TEXT & ~filters.COMMAND,
            search_file
        )
    )

    # Errors
    app.add_error_handler(error_handler)

    print("🔥 HOUSE OF ANIME BOT STARTED!")

    app.run_polling()


# =========================================================
# PROGRAM START
# =========================================================

if __name__ == "__main__":
    main()# =========================================================
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
    main()# =========================================================
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
#
# "example": 25
#
# 25 = private storage channel lo file message ID
#
# Nee files ki tarvata values change cheyyi.
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
# DELETE FILE AFTER 1 HOUR
# =========================================================

async def delete_message_job(context: ContextTypes.DEFAULT_TYPE):

    job = context.job

    try:
        await context.bot.delete_message(
            chat_id=job.data["chat_id"],
            message_id=job.data["message_id"],
        )

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
                "✅ Membership Verified!\n\n"
                "🎬 Ippudu meeku kavalsina "
                "file/anime name type cheyyandi."
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
# SEARCH
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

    # Search
    for name, message_id in FILES.items():

        if search_text in name.lower():

            matched_name = name
            matched_message_id = message_id

            break

    # =====================================================
    # NOT FOUND
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


# =========================================================
# ADMIN APPROVE / REJECT
# =========================================================

async def admin_action(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):

    query = update.callback_query

    # Only admin
    if query.from_user.id != ADMIN_ID:

        await query.answer(
            "❌ Not authorized.",
            show_alert=True
        )

        return

    await query.answer()

    action, request_id = query.data.split("_", 1)

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

            await context.bot.send_message(
                chat_id=user_id,
                text=(
                    "🎉 REQUEST APPROVED! 🎉\n\n"
                    f"📁 {file_name}\n\n"
                    "⚠️ Ee file 1 hour tarvata "
                    "auto-delete avutundi.\n\n"
                    "🔒 Forwarding/Saving restricted."
                )
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
                "Storage channel settings / "
                "message ID check cheyyandi."
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

    # Render web server
    threading.Thread(
        target=run_web_server,
        daemon=True
    ).start()

    # Telegram bot
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

    # Admin buttons
    application.add_handler(
        CallbackQueryHandler(
            admin_action,
            pattern="^(app|rej)_"
        )
    )

    # Search
    application.add_handler(
        MessageHandler(
            filters.TEXT & ~filters.COMMAND,
            handle_search
        )
    )

    # Error
    application.add_error_handler(error_handler)

    print("🔥 HOUSE OF ANIME BOT STARTED!")

    application.run_polling()


# =========================================================
# RUN
# =========================================================

if __name__ == "__main__":
    main()# CONFIGURATION (Environment Variables)
# =========================================================

BOT_TOKEN = os.environ.get("BOT_TOKEN")
ADMIN_ID = os.environ.get("ADMIN_ID")
FORCE_JOIN_LINK = "https://t.me/Madara_217"

if not BOT_TOKEN:
    raise ValueError("BOT_TOKEN environment variable is missing!")

if not ADMIN_ID:
    raise ValueError("ADMIN_ID environment variable is missing!")

try:
    ADMIN_ID = int(ADMIN_ID)
except ValueError:
    raise ValueError("ADMIN_ID must be a numeric Telegram User ID!")


# =========================================================
# ANIME DATABASE (Links Update Cheskondi)
# =========================================================

ANIME_FILES = {
    "demon slayer": "https://t.me/Madara_217/2",
    "spy x family": "https://t.me/Madara_217/3",
    "naruto": "https://t.me/Madara_217/4",
    "one piece": "https://t.me/Madara_217/5",
    "attack on titan": "https://t.me/Madara_217/6",
}

pending_requests = {}


# =========================================================
# AUTO DELETE TASK (1 Hour = 3600 Seconds)
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
        print(f"Failed to delete message: {e}")


# =========================================================
# /START COMMAND
# =========================================================

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):

    keyboard = [
        [
            InlineKeyboardButton(
                "🔥 Join Main Channel 🔥",
                url=FORCE_JOIN_LINK,
            )
        ]
    ]

    reply_markup = InlineKeyboardMarkup(keyboard)
    first_name = update.effective_user.first_name or "User"

    welcome_text = (
        f"Hello {first_name}!\n\n"
        "Welcome to 𝐇𝐎𝐔𝐒𝐄 𝐎𝐅 𝐀𝐍𝐈𝐌𝐄 🫵🏻🌍\n\n"
        "Anime peru type cheyyandi.\n"
        "Admin approval tarvata access message pampabadutundi.\n\n"
        "⚠️ Access message 1 hour tarvata auto-delete avutundi.\n"
        "🔒 Files Forwarding/Saving restricted."
    )

    await update.message.reply_text(
        text=welcome_text,
        reply_markup=reply_markup,
    )


# =========================================================
# ANIME SEARCH & MISSING ALERT
# =========================================================

async def handle_search(update: Update, context: ContextTypes.DEFAULT_TYPE):

    if not update.message or not update.message.text:
        return

    user_text = update.message.text.strip().lower()
    user = update.effective_user
    username = user.username or "No username"

    matched_key = None

    for key in ANIME_FILES:
        if user_text in key:
            matched_key = key
            break

    # --- Store Lo File Leni Samayamlo (Attractive Message & Admin Alert) ---
    if not matched_key:
        missing_text = (
            "✨ ━━━━━━━━━━━━━━━━━━━━ ✨\n"
            "      ❌ **FILE NOT FOUND** ❌\n"
            "✨ ━━━━━━━━━━━━━━━━━━━━ ✨\n\n"
            f"🥺 **Sorry Friend!** Meeru adigina '{update.message.text}' anime store lo ledhu.\n\n"
            "✨ **Don't Worry!** Mee request direct ga Admin ki cherindhi. Fast ga mee kosam upload chestham! ⚡\n\n"
            "⏳ Koncham time ivvandi... Upload avvagane update istham!\n\n"
            "🔥 **Miss Avvakunda Ventane Main Channel Lo Join Avvandi:**\n"
            f"👉 {FORCE_JOIN_LINK}\n\n"
            "✨ ━━━━━━━━━━━━━━━━━━━━ ✨"
        )

        await update.message.reply_text(
            text=missing_text,
            disable_web_page_preview=True
        )

        try:
            await context.bot.send_message(
                chat_id=ADMIN_ID,
                text=(
                    "⚠️ **MISSING ANIME REQUEST**\n\n"
                    f"👤 **User:** {user.first_name}\n"
                    f"🔗 **Username:** @{username}\n"
                    f"🆔 **User ID:** `{user.id}`\n"
                    f"🎬 **Requested Anime:** {update.message.text}"
                ),
            )
        except Exception as e:
            print(f"Failed to send alert to admin: {e}")

        return

    # --- Store Lo File Unte (Admin Approval WorkFlow) ---
    await update.message.reply_text(
        "⏳ Admin permission kosam request pampinchamu..."
    )

    request_id = f"{user.id}_{matched_key}"

    pending_requests[request_id] = {
        "user_id": user.id,
        "anime_key": matched_key,
        "file_url": ANIME_FILES[matched_key],
    }

    admin_keyboard = [
        [
            InlineKeyboardButton(
                "✅ Approve & Send",
                callback_data=f"app_{request_id}",
            ),
            InlineKeyboardButton(
                "❌ Reject",
                callback_data=f"rej_{request_id}",
            ),
        ]
    ]

    await context.bot.send_message(
        chat_id=ADMIN_ID,
        text=(
            "📥 **NEW FILE REQUEST**\n\n"
            f"👤 **User:** {user.first_name}\n"
            f"🔗 **Username:** @{username}\n"
            f"🆔 **User ID:** `{user.id}`\n"
            f"🎬 **Anime:** {matched_key.upper()}"
        ),
        reply_markup=InlineKeyboardMarkup(admin_keyboard),
    )


# =========================================================
# ADMIN ACTION (APPROVE / REJECT)
# =========================================================

async def handle_admin_action(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
):

    query = update.callback_query

    # Security: Admin check
    if query.from_user.id != ADMIN_ID:
        await query.answer(
            "❌ You are not authorized.",
            show_alert=True,
        )
        return

    await query.answer()
    data = query.data

    try:
        action, request_id = data.split("_", 1)
    except ValueError:
        await query.edit_message_text("❌ Invalid request.")
        return

    if request_id not in pending_requests:
        await query.edit_message_text(
            "❌ Ee request already processed or expired."
        )
        return

    request_data = pending_requests.pop(request_id)
    user_id = request_data["user_id"]
    anime_name = request_data["anime_key"].upper()
    file_url = request_data["file_url"]

    # --- APPROVE ---
    if action == "app":
        try:
            sent_message = await context.bot.send_message(
                chat_id=user_id,
                text=(
                    "🎉 **Request Approved!**\n\n"
                    f"🎬 **Anime:** {anime_name}\n\n"
                    f"📁 **Access Link:**\n{file_url}\n\n"
                    "⚠️ Ee message ⏱️ **1 Hour** lo auto-delete ayipothundhi.\n"
                    "🔒 Forwarding & Saving Disabled!"
                ),
                protect_content=True,
            )

            # Auto-Delete Timer (3600 Sec = 1 Hour)
            context.job_queue.run_once(
                delete_message_job,
                when=3600,
                data={
                    "chat_id": user_id,
                    "message_id": sent_message.message_id,
                },
            )

            await query.edit_message_text(
                f"✅ Approved & Sent.\n"
                f"User ID: `{user_id}`\n"
                "⏱ Auto-delete timer: 1 hour"
            )

        except Exception as e:
            print(f"Send error: {e}")
            await query.edit_message_text(
                f"⚠️ Error while sending message:\n{e}"
            )

    # --- REJECT ---
    elif action == "rej":
        try:
            await context.bot.send_message(
                chat_id=user_id,
                text=(
                    f"❌ Your request for **{anime_name}** "
                    "has been rejected by Admin."
                ),
            )
        except Exception as e:
            print(f"Reject notification error: {e}")

        await query.edit_message_text(
            f"❌ Rejected request for {anime_name}"
        )


# =========================================================
# MAIN FUNCTION
# =========================================================

def main():

    # Render keep-alive server initialization
    threading.Thread(
        target=run_web_server,
        daemon=True,
    ).start()

    application = (
        Application.builder()
        .token(BOT_TOKEN)
        .build()
    )

    # Event Handlers
    application.add_handler(CommandHandler("start", start))
    application.add_handler(
        MessageHandler(
            filters.TEXT & ~filters.COMMAND,
            handle_search,
        )
    )
    application.add_handler(CallbackQueryHandler(handle_admin_action))

    print("✅ Bot is online & fully secured!")
    application.run_polling()


if __name__ == "__main__":
    main()
    await update.message.reply_text(
        text=welcome_text,
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
    threading.Thread(target=run_web_server, daemon=True).start()
    
    # Telegram Bot Polling
    app = Application.builder().token(BOT_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    print("Bot is starting...")
    app.run_polling()

if __name__ == "__main__":
    main()
