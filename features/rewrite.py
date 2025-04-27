import os
import requests
import logging
from dotenv import load_dotenv
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    ContextTypes,
    ConversationHandler,
)

# Настройка логирования
logger = logging.getLogger(__name__)

load_dotenv()
FASTAPI_SERVER_URL = os.getenv("FASTAPI_SERVER_URL", "http://localhost:8000")

# Определяем состояния для ConversationHandler
SELECT_STYLE = "rewrite_select_style"
RECEIVE_POST = "rewrite_receive_post"

TELEGRAM_MAX_MESSAGE_LENGTH = 4096

async def send_long_message(update: Update, text: str) -> None:
    """Отправляет длинное сообщение, разбивая его на части, если превышен лимит Telegram."""
    if len(text) <= TELEGRAM_MAX_MESSAGE_LENGTH:
        await update.message.reply_text(text)
        return

    # Разбиваем текст на части по 4096 символов
    parts = []
    current_part = ""
    for line in text.splitlines(keepends=True):
        if len(current_part) + len(line) <= TELEGRAM_MAX_MESSAGE_LENGTH:
            current_part += line
        else:
            parts.append(current_part)
            current_part = line
    if current_part:
        parts.append(current_part)

    # Отправляем каждую часть отдельным сообщением
    for i, part in enumerate(parts, 1):
        await update.message.reply_text(f"Часть {i}/{len(parts)}:\n\n{part}")
        logger.info(f"Отправлена часть {i}/{len(parts)} сообщения")

async def rewrite(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Обработчик команды /rewrite: показывает список стилей."""
    styles_dir = "styles"
    if not os.path.exists(styles_dir):
        await update.message.reply_text("Пока нет сохраненных стилей. Создайте стиль с помощью /newstyle.")
        return ConversationHandler.END

    styles = [d for d in os.listdir(styles_dir) if os.path.isdir(os.path.join(styles_dir, d))]
    if not styles:
        await update.message.reply_text("Пока нет сохраненных стилей. Создайте стиль с помощью /newstyle.")
        return ConversationHandler.END

    keyboard = [
        [InlineKeyboardButton(style, callback_data=f"rewrite_style_{style}")] for style in styles
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text("Выберите стиль для рерайта:", reply_markup=reply_markup)
    logger.info("Показан список стилей для /rewrite")
    return SELECT_STYLE

async def select_style(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Обработчик выбора стиля: сохраняет стиль и запрашивает текст поста."""
    query = update.callback_query
    await query.answer()

    style_name = query.data[len("rewrite_style_"):]
    context.user_data["selected_style"] = style_name

    await query.message.reply_text(
        "Стиль выбран! Теперь отправьте текст поста (или перешлите пост), который нужно переписать."
    )
    logger.info(f"Стиль '{style_name}' выбран для рерайта")
    return RECEIVE_POST

async def receive_post(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Обработчик получения текста: вызывает API для рерайта и отправляет результат."""
    style_name = context.user_data.get("selected_style")
    if not style_name:
        await update.message.reply_text("Стиль не выбран. Попробуйте снова с /rewrite.")
        return ConversationHandler.END

    # Получаем текст поста
    post_text = update.message.text
    if not post_text:
        await update.message.reply_text("Пожалуйста, отправьте текст для рерайта.")
        return RECEIVE_POST

    # Загружаем данные стиля
    style_dir = os.path.join("styles", style_name)
    meta_file = os.path.join(style_dir, f"{style_name}.meta")
    example_file = os.path.join(style_dir, f"{style_name}.txt")

    if not os.path.exists(meta_file) or not os.path.exists(example_file):
        await update.message.reply_text(f"Стиль '{style_name}' не найден.")
        return ConversationHandler.END

    try:
        # Читаем промпт из .meta файла
        with open(meta_file, "r", encoding="utf-8") as f:
            lines = f.readlines()
            prompt = next(
                (line.split("Prompt: ")[1].strip() for line in lines if line.startswith("Prompt: ")),
                None
            )
        if not prompt:
            await update.message.reply_text("Промпт для стиля не найден.")
            return ConversationHandler.END

        # Уточняем промпт, чтобы он соответствовал стилю .txt файла
        system_prompt = (
            f"{prompt}"
        )

        # Читаем пример текста из .txt файла
        with open(example_file, "r", encoding="utf-8") as f:
            example_lines = f.readlines()
            # Берём только первые 100 строк, чтобы уменьшить шум
            example_lines = example_lines[:100]
            example_text = "".join(example_lines).strip()

        # Логируем содержимое .txt файла для отладки
        logger.info(f"Содержимое примера (.txt): {example_text[:500]}... (обрезано до 500 символов)")

    except Exception as e:
        await update.message.reply_text(f"Ошибка при чтении данных стиля: {e}")
        return ConversationHandler.END

    # Формируем запрос к OpenRouter API
    try:
        # Отправляем запрос к FastAPI
        response = requests.post(
            f"{FASTAPI_SERVER_URL}/rewrite",
            json={
                "system_prompt": system_prompt,
                "example_text": example_text,
                "post_text": post_text
            }
        )

        # Проверяем статус ответа
        if response.status_code != 200:
            error_details = response.json().get("detail", "Неизвестная ошибка")
            raise Exception(f"Ошибка FastAPI-сервера (status {response.status_code}): {error_details}")

        result = response.json()
        logger.info(f"Ответ от FastAPI: {result}")

        rewritten_text = result["rewritten_text"]

        # Отправляем переписанный текст, разбивая на части, если нужно
        await send_long_message(update, f"Переписанный текст:\n\n{rewritten_text}")
        logger.info("Текст успешно переписан")

    except Exception as e:
        await update.message.reply_text(f"Ошибка при рерайте текста: {e}")
        logger.error(f"Ошибка при рерайте: {e}")
        return ConversationHandler.END

    context.user_data.clear()
    return ConversationHandler.END

async def cancel_rewrite(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Обработчик отмены команды /rewrite."""
    await update.message.reply_text("Рерайт отменён.")
    context.user_data.clear()
    return ConversationHandler.END
