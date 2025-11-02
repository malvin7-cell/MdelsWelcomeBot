# bot.py (final webhook version)
import os
import logging
from dotenv import load_dotenv
from telegram import Update, Bot
from telegram.ext import ApplicationBuilder, MessageHandler, ContextTypes, filters

load_dotenv()
TOKEN = os.environ.get("TELEGRAM_TOKEN")
WELCOME_FILE = os.environ.get("WELCOME_FILE", "welcome.txt").strip()
PORT = int(os.environ.get("PORT", 8000))
WEBHOOK_SECRET = os.environ.get("WEBHOOK_SECRET", TOKEN)
WEBHOOK_PATH = os.environ.get("WEBHOOK_PATH", f"/webhook/{WEBHOOK_SECRET}")
EXTERNAL_URL = os.environ.get("RENDER_EXTERNAL_URL") or os.environ.get("EXTERNAL_URL") or ""

logging.basicConfig(format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO)
logger = logging.getLogger(__name__)

def load_welcome_message():
    try:
        if os.path.exists(WELCOME_FILE):
            with open(WELCOME_FILE, "r", encoding="utf-8") as f:
                return f.read()
    except Exception:
        logger.exception("Failed to read welcome file")
    return os.environ.get("WELCOME_MESSAGE", "👋 Selamat datang, {first_name}!")

WELCOME_TEMPLATE = load_welcome_message()

async def welcome_new_members(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message:
        return
    for member in (update.message.new_chat_members or []):
        if member.is_bot:
            continue
        first = member.first_name or ""
        text = WELCOME_TEMPLATE.format(first_name=first, chat_title=update.effective_chat.title or "grup ini")
        try:
            await update.message.reply_text(text)
        except Exception:
            logger.exception("Failed to send welcome message")

async def error_handler(update: object, context: ContextTypes.DEFAULT_TYPE):
    logger.error("Error while handling update", exc_info=context.error)

def build_app(token: str):
    app = ApplicationBuilder().token(token).build()
    app.add_handler(MessageHandler(filters.StatusUpdate.NEW_CHAT_MEMBERS, welcome_new_members))
    app.add_error_handler(error_handler)
    return app

def main():
    if not TOKEN:
        raise RuntimeError("TELEGRAM_TOKEN not set")

    if not EXTERNAL_URL:
        raise RuntimeError("EXTERNAL_URL (public URL) not set as env var. On Render set RENDER_EXTERNAL_URL or EXTERNAL_URL to your service URL (e.g. https://your-app.onrender.com)")

    app = build_app(TOKEN)
    bot = Bot(TOKEN)

    full_webhook = EXTERNAL_URL.rstrip("/") + WEBHOOK_PATH
    logger.info("Webhook URL will be: %s", full_webhook)

    # Delete previous webhook if any
    try:
        bot.delete_webhook()
    except Exception:
        pass

    # set webhook at Telegram with secret token
    set_ok = bot.set_webhook(url=full_webhook, secret_token=WEBHOOK_SECRET)
    if not set_ok:
        logger.error("Failed to set webhook")
        raise RuntimeError("set_webhook failed")

    # run a webhook server built into PTB
    # Note: Application.run_webhook will start an HTTP server listening on given host/port/path.
    logger.info("Starting webhook server (port=%s, path=%s)", PORT, WEBHOOK_PATH)
    # stop_signals=None prevents PTB from handling signals; Render will manage process lifecycle
    app.run_webhook(listen="0.0.0.0", port=PORT, path=WEBHOOK_PATH, webhook_url=full_webhook, secret_token=WEBHOOK_SECRET)

if __name__ == "__main__":
    main()
