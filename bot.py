from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, ContextTypes, filters
import secrets
import sqlite3
import os

# ===== ENV VARIABLES =====
BOT_TOKEN = os.environ.get("TOKEN")  # Your bot token from Railway/Host
ADMIN_ID = int(os.environ.get("ADMIN_ID", "8411281881"))  # Default admin if not set
# ========================

# ===== DATABASE SETUP =====
conn = sqlite3.connect("files.db", check_same_thread=False)
cursor = conn.cursor()

cursor.execute("""
CREATE TABLE IF NOT EXISTS files (
    code TEXT PRIMARY KEY,
    file_id TEXT,
    file_type TEXT
)
""")
conn.commit()
# ==========================


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if context.args:
        code = context.args[0]

        cursor.execute("SELECT file_id, file_type FROM files WHERE code = ?", (code,))
        result = cursor.fetchone()

        if result:
            file_id, file_type = result
            chat_id = update.effective_chat.id

            if file_type == "document":
                await context.bot.send_document(chat_id, file_id)

            elif file_type == "video":
                await context.bot.send_video(chat_id, file_id)

            elif file_type == "photo":
                await context.bot.send_photo(chat_id, file_id)

            elif file_type == "audio":
                await context.bot.send_audio(chat_id, file_id)

        else:
            await update.message.reply_text("❌ Invalid or expired link.")
    else:
        await update.message.reply_text(
            "✅ File Store Bot is Running!\n\n"
            "Send a valid file link to get content."
        )


async def file_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.message.from_user.id

    if user_id != ADMIN_ID:
        await update.message.reply_text("❌ Only admin can upload.")
        return

    file_id = None
    file_type = None

    if update.message.document:
        file_id = update.message.document.file_id
        file_type = "document"

    elif update.message.video:
        file_id = update.message.video.file_id
        file_type = "video"

    elif update.message.photo:
        file_id = update.message.photo[-1].file_id
        file_type = "photo"

    elif update.message.audio:
        file_id = update.message.audio.file_id
        file_type = "audio"

    else:
        await update.message.reply_text("❌ Unsupported file type.")
        return

    code = secrets.token_hex(4)

    cursor.execute(
        "INSERT INTO files (code, file_id, file_type) VALUES (?, ?, ?)",
        (code, file_id, file_type)
    )
    conn.commit()

    bot_username = (await context.bot.get_me()).username
    deep_link = f"https://t.me/{bot_username}?start={code}"

    await update.message.reply_text(
        f"✅ File Stored Permanently!\n\n"
        f"🔗 Share Link:\n{deep_link}"
    )


def main():
    app = Application.builder().token(BOT_TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.ALL, file_handler))

    print("✅ Permanent File Store Bot Running...")
    app.run_polling()


if __name__ == "__main__":
    main()
