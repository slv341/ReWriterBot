from telegram import Update
from telegram.ext import ContextTypes

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await update.message.reply_text(
        "Привет! Я бот для рерайта постов. Используй /newstyle, чтобы создать новый стиль, "
        "/liststyles, чтобы посмотреть сохраненные стили."
    )
