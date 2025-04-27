import os
import shutil
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes


async def menu(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    commands = [
        "/start - Начать работу с ботом",
        "/newstyle - Создать новый стиль рерайта",
        "/liststyles - Показать все сохраненные стили",
    ]
    await update.message.reply_text("Доступные команды:\n" + "\n".join(commands))

async def button_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query
    await query.answer()

    callback_data = query.data
    if callback_data.startswith("style_"):
        style_name = callback_data[len("style_"):]
        style_dir = os.path.join("styles", style_name)
        meta_file = os.path.join(style_dir, f"{style_name}.meta")
        
        if not os.path.exists(meta_file):
            await query.message.reply_text(f"Стиль '{style_name}' не найден.")
            return

        try:
            with open(meta_file, "r", encoding="utf-8") as f:
                lines = f.readlines()
                prompt = next(
                    (line.split("Prompt: ")[1].strip() for line in lines if line.startswith("Prompt: ")),
                    "Промпт не найден"
                )
        except Exception as e:
            await query.message.reply_text(f"Ошибка при чтении промпта: {e}")
            return

        keyboard = [
            [InlineKeyboardButton("Удалить", callback_data=f"delete_style_{style_name}")],
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await query.message.reply_text(f"Стиль: {style_name}\nПромпт: {prompt}", reply_markup=reply_markup)
    
    elif callback_data.startswith("delete_style_"):
        style_name = callback_data[len("delete_style_"):]
        style_dir = os.path.join("styles", style_name)
        
        if not os.path.exists(style_dir):
            await query.message.reply_text(f"Стиль '{style_name}' не найден.")
            return
        
        try:
            shutil.rmtree(style_dir)
            await query.message.reply_text(f"Стиль '{style_name}' успешно удален.")
        except Exception as e:
            await query.message.reply_text(f"Ошибка при удалении стиля: {e}")