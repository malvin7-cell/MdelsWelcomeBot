# bot.py
import os
import time
import logging
import traceback
from dotenv import load_dotenv
from telegram import Update
from telegram.ext import (
    ApplicationBuilder,
    MessageHandler,
    ContextTypes,
    filters,
)

# ---- Config & load env ----
load_dotenv()
TOKEN = os.environ.get("TELEGRAM_TOKEN")
WELCOME_FILE = os.environ.get("WELCOME_FILE", "").strip()

# ----- Logging -----
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO,
)
logger = logging.getLogger(__name__)

# ----- Read welcome message (from file if provided) -----
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

def load_welcome_message():
    # Prioritize reading WELCOME_FILE if set and exists, else fallback to env var
    if WELCOME_FILE:
        welcome_path = os.path.join(BASE_DIR, WELCOME_FILE)
        logger.info("Trying to read welcome file at: %s", welcome_path)
        try:
            if os.path.exists(welcome_path):
                with open(welcome_path, "r", encoding="utf-8") as f:
                    return f.read()
            else:
                logger.warning("WELCOME_FILE not found at %s, falling back.", welcome_path)
        except Exception as e:
            logger.exception("Failed to read welcome file: %s", e)

    # fallback to WELCOME_MESSAGE env var
    env_msg = os.environ.get("WELCOME_MESSAGE", "👋 Selamat datang, {first_name} di {chat_title}!")
    # if env contains literal \n sequences (from .env), convert to actual newlines
    return env_msg.replace("\\n", "\n")

# global template (initial load)
WELCOME_MESSAGE_TEMPLATE = load_welcome_message()

# ----- Handlers -----
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
        # reload message each join so edits to welcome.txt apply without restart
        template = load_welcome_message()
        text = template.format(first_name=first, username=username, chat_title=chat_title)
        try:
            await update.message.reply_text(text)
        except Exception as e:
            logger.exception("Gagal mengirim welcome message: %s", e)

async def error_handler(update: object, context: ContextTypes.DEFAULT_TYPE):
    logger.error("Exception terjadi:", exc_info=context.error)

# ----- Factory to create Application -----
def build_app(token: str):
    app = ApplicationBuilder().token(token).build()
    app.add_handler(MessageHandler(filters.StatusUpdate.NEW_CHAT_MEMBERS, welcome_new_members))
    app.add_error_handler(error_handler)
    return app

# ----- Main with auto-restart logic -----
def main():
    if not TOKEN:
        raise RuntimeError("TELEGRAM_TOKEN belum di-set di .env / environment variables")

    max_backoff = 300  # maximum backoff seconds (5 minutes)
    backoff = 5        # initial backoff seconds

    while True:
        try:
            logger.info("Starting Telegram bot application...")
            app = build_app(TOKEN)
            # run_polling() blocks until it stops (or raises)
            app.run_polling()
            # If run_polling returns normally (e.g., shutdown), break loop
            logger.info("Application stopped normally (run_polling returned). Exiting loop.")
            break
        except KeyboardInterrupt:
            logger.info("KeyboardInterrupt received — exiting.")
            try:
                # give library chance to shutdown cleanly
                app.stop()
            except Exception:
                pass
            break
        except Exception as e:
            # Log full traceback
            logger.error("Unhandled exception in bot: %s", e)
            traceback.print_exc()
            logger.info("Bot will attempt to restart in %s seconds...", backoff)
            time.sleep(backoff)
            # Exponential backoff with cap
            backoff = min(backoff * 2, max_backoff)
            # loop continues and rebuild app
            logger.info("Restarting bot now...")

# ----- Main with auto-restart logic -----
def main():
    if not TOKEN:
        raise RuntimeError("TELEGRAM_TOKEN belum di-set di .env / environment variables")

    # Ambil nilai backoff dari environment (bisa diatur di Render)
    backoff = int(os.getenv("BACKOFF_INITIAL", 5))       # default 5 detik
    max_backoff = int(os.getenv("BACKOFF_MAX", 300))     # default 5 menit

    while True:
        try:
            logger.info("Starting Telegram bot...")
            app = ApplicationBuilder().token(TOKEN).build()

            # Tambahkan handler kamu di sini
            app.add_handler(MessageHandler(filters.StatusUpdate.NEW_CHAT_MEMBERS, welcome_new_members))
            app.add_error_handler(error_handler)

            # Jalankan polling (stop_signals=None agar tidak berhenti otomatis)
            app.run_polling(stop_signals=None)
            logger.warning("run_polling() returned — restarting bot automatically...")
        except Exception as e:
            logger.exception("Bot crashed with exception: %s", e)

        # Delay sebelum restart (backoff)
        logger.info(f"Bot will restart in {backoff} seconds...")
        time.sleep(backoff)
        backoff = min(backoff * 2, max_backoff)
        logger.info("Restarting bot now...")


if __name__ == "__main__":
    main()



