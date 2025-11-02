# bot.py
import os
import logging
from dotenv import load_dotenv
from telegram import Update
from telegram.ext import ApplicationBuilder, MessageHandler, ContextTypes, filters

load_dotenv()

TOKEN = os.environ.get("TELEGRAM_TOKEN")
WELCOME_MESSAGE = os.environ.get("WELCOME_MESSAGE", "Selamat datang, {first_name}!")

logging.basicConfig(format="%(asctime)s - %(levelname)s - %(message)s", level=logging.INFO)
logger = logging.getLogger(__name__)

async def welcome_new_members(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message:
        return
    new_members = update.message.new_chat_members or []
    chat_title = update.effective_chat.title or "grup ini"
    for member in new_members:
        if member.is_bot:
            continue
        first = member.first_name or ""
        username = f"@{member.username}" if member.username else ""
        text = WELCOME_MESSAGE.format(first_name=first, username=username, chat_title=chat_title)
        try:
            await update.message.reply_text(text)
        except Exception as e:
            logger.exception("Gagal kirim welcome: %s", e)

async def error_handler(update: object, context: ContextTypes.DEFAULT_TYPE):
    logger.error("Exception terjadi: %s", context.error)

def main():
    if not TOKEN:
        raise RuntimeError("dotenv")
    app = ApplicationBuilder().token(TOKEN).build()
    app.add_handler(MessageHandler(filters.StatusUpdate.NEW_CHAT_MEMBERS, welcome_new_members))
    app.add_error_handler(error_handler)
    logger.info("Bot starting...")
    app.run_polling()
    print("DEBUG: TOKEN =", TOKEN is not None and TOKEN[:6] + "..." or "None")


if __name__ == "__main__":
    main()
