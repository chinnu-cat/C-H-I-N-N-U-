import os
import sqlite3
import secrets
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
# SETTINGS
# =========================================================

BOT_TOKEN = os.environ.get("BOT_TOKEN")
ADMIN_ID = int(os.environ.get("ADMIN_ID", "0"))

MAIN_CHANNEL = "@madara_217"
MAIN_CHANNEL_LINK = "https://t.me/madara_217"

DB_FILE = "anime_bot.db"


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

    server = HTTPServer(
        ("0.0.0.0", port),
        HealthHandler
    )

    server.serve_forever()


# =========================================================
# DATABASE
# =========================================================

def db():
    return sqlite3.connect(DB_FILE)


def init_db():

    conn = db()
    cur = conn.cursor()

    cur.execute("""
        CREATE TABLE IF NOT EXISTS requests (
            request_id TEXT PRIMARY KEY,
            user_id INTEGER NOT NULL,
            user_name TEXT,
            anime TEXT NOT NULL,
            requirement TEXT NOT NULL,
            status TEXT NOT NULL DEFAULT 'pending',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

    conn.commit()
    conn.close()


def save_request(
    request_id,
    user_id,
    user_name,
    anime,
    requirement
):

    conn = db()
    cur = conn.cursor()

    cur.execute("""
        INSERT INTO requests
        (
            request_id,
            user_id,
            user_name,
            anime,
            requirement,
            status
        )
        VALUES (?, ?, ?, ?, ?, 'pending')
    """, (
        request_id,
        user_id,
        user_name,
        anime,
        requirement
    ))

    conn.commit()
    conn.close()


def get_request(request_id):

    conn = db()
    cur = conn.cursor()

    cur.execute("""
        SELECT
            request_id,
            user_id,
            user_name,
            anime,
            requirement,
            status
        FROM requests
        WHERE request_id = ?
    """, (request_id,))

    result = cur.fetchone()

    conn.close()

    return result


def update_status(request_id, status):

    conn = db()
    cur = conn.cursor()

    cur.execute("""
        UPDATE requests
        SET status = ?
        WHERE request_id = ?
    """, (
        status,
        request_id
    ))

    conn.commit()
    conn.close()


# =========================================================
# ANIME DATABASE
# =========================================================

ANIME_LIST = [
    "Naruto",
    "Naruto Shippuden",
    "Death Note",
    "Attack on Titans",
    "Solo Leveling",
    "Jujutsu Kaisen",
    "Spy x Family",
    "Demon Slayer",
]


def find_anime(text):

    search = text.strip().lower()

    for anime in ANIME_LIST:

        if search == anime.lower():
            return anime

    for anime in ANIME_LIST:

        if search in anime.lower():
            return anime

    return None


# =========================================================
# START
# =========================================================

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):

    keyboard = [

        [
            InlineKeyboardButton(
                "🔥 JOIN OFFICIAL CHANNEL 🔥",
                url=MAIN_CHANNEL_LINK
            )
        ],

        [
            InlineKeyboardButton(
                "✅ I JOINED",
                callback_data="check_join"
            )
        ]

    ]

    await update.message.reply_text(

        "🎬 WELCOME TO HOUSE OF ANIME 🫵🏻🌍\n\n"

        "🔥 Search your favourite anime\n"
        "📥 Send your requirement\n"
        "⏳ Admin approval required\n\n"

        "📢 First join our Official Channel.\n\n"

        "👇🏻 Join now and continue.",

        reply_markup=InlineKeyboardMarkup(keyboard)
    )


# =========================================================
# JOIN CHECK
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

                "✅ JOINED SUCCESSFULLY!\n\n"

                "📁 Ippudu meeku kavalsina anime name "
                "type cheyyandi.\n\n"

                "Example:\n"
                "Solo Leveling\n"
                "Naruto\n"
                "Demon Slayer"

            )

        else:

            keyboard = [[
                InlineKeyboardButton(
                    "🔥 JOIN OFFICIAL CHANNEL 🔥",
                    url=MAIN_CHANNEL_LINK
                )
            ]]

            await query.message.reply_text(

                "❌ YOU HAVE NOT JOINED YET.\n\n"
                "First join our Official Channel.",

                reply_markup=InlineKeyboardMarkup(keyboard)
            )

    except Exception as e:

        print("JOIN CHECK ERROR:", e)

        await query.message.reply_text(
            "⚠️ Unable to check membership.\n"
            "Please try again."
        )


# =========================================================
# SEARCH / REQUEST
# =========================================================

async def search_anime(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):

    if not update.message:
        return

    text = update.message.text.strip()

    anime = find_anime(text)

    if anime is None:

        await update.message.reply_text(

            "❌ ANIME NOT FOUND\n\n"

            f"📁 You searched: {text}\n\n"

            "Please check the spelling and try again."

        )

        return

    context.user_data["selected_anime"] = anime

    await update.message.reply_text(

        f"📁 {anime}\n\n"

        "✅ Anime found!\n\n"

        "📦 Now send your requirement.\n\n"

        "Example:\n"
        "Season 2 • Episodes 1-13 • Dual Audio\n\n"

        "You can type your exact requirement below."

    )


# =========================================================
# REQUIREMENT SUBMISSION
# =========================================================

async def submit_requirement(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):

    if not update.message:
        return

    anime = context.user_data.get("selected_anime")

    if not anime:

        return

    requirement = update.message.text.strip()

    if not requirement:

        await update.message.reply_text(
            "❌ Please enter your requirement."
        )

        return

    user = update.effective_user

    request_id = secrets.token_hex(6)

    save_request(
        request_id=request_id,
        user_id=user.id,
        user_name=user.first_name or "Unknown",
        anime=anime,
        requirement=requirement
    )

    # =====================================================
    # USER MESSAGE
    # =====================================================

    keyboard = [[
        InlineKeyboardButton(
            "🔥 JOIN OFFICIAL CHANNEL 🔥",
            url=MAIN_CHANNEL_LINK
        )
    ]]

    await update.message.reply_text(

        "✅ YOUR REQUEST HAS BEEN SUBMITTED!\n\n"

        f"📁 Anime: {anime}\n"
        f"📦 Requirement: {requirement}\n\n"

        "📩 Your request has been sent to our Admin.\n\n"

        "⏳ Please wait for Admin response.\n\n"

        "📢 Meanwhile, join our Official Channel\n"
        "for latest anime updates & announcements.\n\n"

        "👇🏻",

        reply_markup=InlineKeyboardMarkup(keyboard)
    )

    # =====================================================
    # ADMIN MESSAGE
    # =====================================================

    admin_keyboard = [[

        InlineKeyboardButton(
            "✅ APPROVE",
            callback_data=f"approve:{request_id}"
        ),

        InlineKeyboardButton(
            "❌ REJECT",
            callback_data=f"reject:{request_id}"
        )

    ]]

    try:

        await context.bot.send_message(

            chat_id=ADMIN_ID,

            text=(

                "🔔 NEW ANIME REQUEST\n\n"

                f"👤 User: {user.first_name or 'Unknown'}\n"
                f"🆔 User ID: {user.id}\n\n"

                f"📁 Anime: {anime}\n"
                f"📦 Requirement: {requirement}\n\n"

                "⏳ Waiting for Admin decision."

            ),

            reply_markup=InlineKeyboardMarkup(
                admin_keyboard
            )
        )

    except Exception as e:

        print("ADMIN MESSAGE ERROR:", e)


# =========================================================
# ADMIN APPROVE / REJECT
# =========================================================

async def admin_action(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):

    query = update.callback_query

    # -----------------------------------------------------
    # ADMIN ONLY
    # -----------------------------------------------------

    if query.from_user.id != ADMIN_ID:

        await query.answer(
            "❌ You are not authorized.",
            show_alert=True
        )

        return

    await query.answer()

    try:

        action, request_id = query.data.split(":", 1)

    except ValueError:

        await query.edit_message_text(
            "❌ Invalid request."
        )

        return

    request = get_request(request_id)

    if not request:

        await query.edit_message_text(
            "⚠️ Request not found."
        )

        return

    (
        request_id,
        user_id,
        user_name,
        anime,
        requirement,
        status
    ) = request

    # -----------------------------------------------------
    # ALREADY PROCESSED
    # -----------------------------------------------------

    if status != "pending":

        await query.edit_message_text(

            "⚠️ REQUEST ALREADY PROCESSED\n\n"

            f"📁 Anime: {anime}\n"
            f"📦 Requirement: {requirement}\n"
            f"📌 Status: {status.upper()}"

        )

        return

    # =====================================================
    # APPROVE
    # =====================================================

    if action == "approve":

        update_status(
            request_id,
            "approved"
        )

        try:

            await context.bot.send_message(

                chat_id=user_id,

                text=(

                    "✅ REQUEST APPROVED\n\n"

                    f"📁 Anime: {anime}\n"
                    f"📦 Requirement: {requirement}\n\n"

                    "🎉 Your request has been approved.\n\n"

                    "⏳ Your authorized files are being prepared..."

                )

            )

        except Exception as e:

            print("APPROVAL USER MESSAGE ERROR:", e)

        await query.edit_message_text(

            "✅ REQUEST APPROVED\n\n"

            f"👤 User: {user_name}\n"
            f"🆔 User ID: {user_id}\n\n"

            f"📁 Anime: {anime}\n"
            f"📦 Requirement: {requirement}"

        )

    # =====================================================
    # REJECT
    # =====================================================

    elif action == "reject":

        update_status(
            request_id,
            "rejected"
        )

        keyboard = [[

            InlineKeyboardButton(
                "🔥 JOIN OFFICIAL CHANNEL 🔥",
                url=MAIN_CHANNEL_LINK
            )

        ]]

        try:

            await context.bot.send_message(

                chat_id=user_id,

                text=(

                    "❌ REQUEST REJECTED\n\n"

                    f"📁 Anime: {anime}\n"
                    f"📦 Requirement: {requirement}\n\n"

                    "The requested files are currently "
                    "not available with us.\n\n"

                    "🙏 Don't be disappointed!\n\n"

                    "📩 Your message and requirement have "
                    "reached our Boss/Admin.\n\n"

                    "🔥 We will try our best to upload "
                    "the requested anime\n"
                    "when it becomes available.\n\n"

                    "Thank you for your patience and support. ❤️\n\n"

                    "📢 Stay Connected With Us\n\n"

                    "🔥 Join our Official Channel for\n"
                    "new anime updates & announcements.\n\n"

                    "👇🏻\n"
                    "🔥 JOIN OFFICIAL CHANNEL 🔥"

                ),

                reply_markup=InlineKeyboardMarkup(
                    keyboard
                )

            )

        except Exception as e:

            print("REJECTION USER MESSAGE ERROR:", e)

        await query.edit_message_text(

            "❌ REQUEST REJECTED\n\n"

            f"👤 User: {user_name}\n"
            f"🆔 User ID: {user_id}\n\n"

            f"📁 Anime: {anime}\n"
            f"📦 Requirement: {requirement}"

        )


# =========================================================
# ADMIN /START TEST
# =========================================================

async def admin_test(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):

    if update.effective_user.id != ADMIN_ID:
        return

    await update.message.reply_text(
        "👑 ADMIN ACCESS CONFIRMED\n\n"
        "🔥 HOUSE OF ANIME BOT IS RUNNING!"
    )


# =========================================================
# ERROR HANDLER
# =========================================================

async def error_handler(
    update: object,
    context: ContextTypes.DEFAULT_TYPE
):

    print(
        "BOT ERROR:",
        context.error
    )


# =========================================================
# MAIN
# =========================================================

def main():

    if not BOT_TOKEN:

        print("❌ BOT_TOKEN missing")

        return

    init_db()

    threading.Thread(
        target=run_server,
        daemon=True
    ).start()

    app = (
        Application
        .builder()
        .token(BOT_TOKEN)
        .build()
    )

    # COMMANDS

    app.add_handler(
        CommandHandler(
            "start",
            start
        )
    )

    app.add_handler(
        CommandHandler(
            "admintest",
            admin_test
        )
    )

    # JOIN CHECK

    app.add_handler(
        CallbackQueryHandler(
            check_join,
            pattern=r"^check_join$"
        )
    )

    # ADMIN APPROVE / REJECT

    app.add_handler(
        CallbackQueryHandler(
            admin_action,
            pattern=r"^(approve|reject):"
        )
    )

    # TEXT

    app.add_handler(
        MessageHandler(
            filters.TEXT & ~filters.COMMAND,
            text_router
        )
    )

    app.add_error_handler(
        error_handler
    )

    print(
        "🔥 HOUSE OF ANIME BOT STARTED!"
    )

    app.run_polling()


# =========================================================
# TEXT ROUTER
# =========================================================

async def text_router(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):

    if not update.message:
        return

    # If user already selected anime,
    # next text is treated as requirement.

    if context.user_data.get("selected_anime"):

        await submit_requirement(
            update,
            context
        )

    else:

        await search_anime(
            update,
            context
        )


# =========================================================
# RUN
# =========================================================

if __name__ == "__main__":
    main()
