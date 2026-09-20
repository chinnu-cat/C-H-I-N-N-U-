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
# WEB SERVER - Render Health Check
# =========================================================

class HealthCheckHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.send_header("Content-Type", "text/plain")
        self.end_headers()
        self.wfile.write(b"Bot is Running Alive!")

    def log_message(self, format, *args):
        pass


def run_web_server():
    port = int(os.environ.get("PORT", "8080"))
    server = HTTPServer(("0.0.0.0", port), HealthCheckHandler)
    server.serve_forever()


# =========================================================
# CONFIGURATION (Environment Variables)
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
