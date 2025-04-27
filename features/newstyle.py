import os
import re
from telegram import Update
from telegram.ext import ContextTypes, ConversationHandler

# Определяем состояния для ConversationHandler
PROMPT = "newstyle_prompt"
EXAMPLE = "newstyle_example"
STYLE_NAME = "newstyle_style_name"

async def new_style(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    await update.message.reply_text(
        "Введите системный промпт для ИИ (например, 'Пиши в деловом стиле, коротко и четко')."
    )
    return PROMPT

async def receive_prompt(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    context.user_data["prompt"] = update.message.text
    await update.message.reply_text(
        "Теперь отправьте .txt файл с примером текста для стиля."
    )
    return EXAMPLE

async def receive_example(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    if not update.message.document or not update.message.document.file_name.endswith(".txt"):
        await update.message.reply_text("Пожалуйста, отправьте файл с расширением .txt.")
        return EXAMPLE

    file = await update.message.document.get_file()
    file_name = update.message.document.file_name
    temp_file_path = os.path.join("styles", file_name)
    
    try:
        await file.download_to_drive(temp_file_path)
        context.user_data["example_file"] = temp_file_path
    except Exception as e:
        await update.message.reply_text(f"Ошибка при сохранении файла: {e}")
        return EXAMPLE
    
    await update.message.reply_text("Введите название стиля (например, 'Деловой').")
    return STYLE_NAME

async def receive_style_name(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    style_name = re.sub(r'[^\w\s-]', '', update.message.text).replace(" ", "_")
    if not style_name:
        await update.message.reply_text(
            "Название стиля не может быть пустым или содержать только недопустимые символы. Попробуйте снова."
        )
        return STYLE_NAME

    prompt = context.user_data.get("prompt")
    temp_file_path = context.user_data.get("example_file")
    
    style_dir = os.path.join("styles", style_name)
    try:
        os.makedirs(style_dir, exist_ok=True)
        
        example_file_name = f"{style_name}.txt"
        example_file_path = os.path.join(style_dir, example_file_name)
        os.rename(temp_file_path, example_file_path)
        
        style_data = f"Style: {style_name}\nPrompt: {prompt}\nExample: {example_file_name}\n"
        style_file = os.path.join(style_dir, f"{style_name}.meta")
        
        with open(style_file, "w", encoding="utf-8") as f:
            f.write(style_data)
        
        await update.message.reply_text(f"Стиль '{style_name}' успешно сохранен!")
    except Exception as e:
        await update.message.reply_text(f"Ошибка при сохранении стиля: {e}")
        if os.path.exists(temp_file_path):
            os.remove(temp_file_path)
        return ConversationHandler.END
    
    context.user_data.clear()
    return ConversationHandler.END

async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    await update.message.reply_text("Создание стиля отменено.")
    temp_file_path = context.user_data.get("example_file")
    if temp_file_path and os.path.exists(temp_file_path):
        os.remove(temp_file_path)
    context.user_data.clear()
    return ConversationHandler.END
