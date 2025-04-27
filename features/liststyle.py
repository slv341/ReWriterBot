import os
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, BotCommand
from telegram.ext import ContextTypes


async def list_styles(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    styles_dir = "styles"
    if not os.path.exists(styles_dir):
        await update.message.reply_text("Пока нет сохраненных стилей. Создайте стиль с помощью /newstyle.")
        return

    styles = [d for d in os.listdir(styles_dir) if os.path.isdir(os.path.join(styles_dir, d))]
    if not styles:
        await update.message.reply_text("Пока нет сохраненных стилей. Создайте стиль с помощью /newstyle.")
        return

    keyboard = [
        [InlineKeyboardButton(style, callback_data=f"style_{style}")] for style in styles
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text("Тут отображены все ваши стили:", reply_markup=reply_markup)
