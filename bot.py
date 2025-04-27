import os
import logging
from features.start import start
from features.menu import menu, button_callback
from features.newstyle import new_style, receive_prompt, receive_example, receive_style_name, cancel
from features.liststyle import list_styles
from features.rewrite import rewrite, select_style, receive_post, cancel_rewrite
from typing import Optional
from dotenv import load_dotenv
from telegram import BotCommand
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    CallbackQueryHandler,
    filters,
    ConversationHandler
)

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Загружаем переменные из .env
load_dotenv()
BOT_TOKEN: Optional[str] = os.getenv("BOT_TOKEN")
if not BOT_TOKEN:
    raise ValueError("BOT_TOKEN not found in .env file")

# Определяем состояния для ConversationHandler
PROMPT = "newstyle_prompt"
EXAMPLE = "newstyle_example"
STYLE_NAME = "newstyle_style_name"
SELECT_STYLE = "rewrite_select_style"
RECEIVE_POST = "rewrite_receive_post"

async def post_init(application: Application) -> None:
    """Хук для регистрации команд после инициализации приложения."""
    commands = [
        BotCommand("start", "Начать работу с ботом"),
        BotCommand("newstyle", "Создать новый стиль рерайта"),
        BotCommand("liststyles", "Показать все сохраненные стили"),
        BotCommand("rewrite", "Переписать текст в выбранном стиле"),
    ]
    try:
        await application.bot.set_my_commands(commands)
        logger.info("Команды успешно зарегистрированы: %s", [cmd.command for cmd in commands])
    except Exception as e:
        logger.error("Ошибка при регистрации команд: %s", e)

# Настройка логирования
def main() -> None:
    os.makedirs("styles", exist_ok=True)
    
    application = Application.builder().token(BOT_TOKEN).post_init(post_init).build()
    
    new_style_handler = ConversationHandler(
        entry_points=[CommandHandler("newstyle", new_style)],
        states={
            PROMPT: [MessageHandler(filters.TEXT & ~filters.COMMAND, receive_prompt)],
            EXAMPLE: [MessageHandler(filters.Document.ALL, receive_example)],
            STYLE_NAME: [MessageHandler(filters.TEXT & ~filters.COMMAND, receive_style_name)],
        },
        fallbacks=[CommandHandler("cancel", cancel)],
    )

    rewrite_handler = ConversationHandler(
        entry_points=[CommandHandler("rewrite", rewrite)],
        states={
            SELECT_STYLE: [CallbackQueryHandler(select_style, pattern="^rewrite_style_")],
            RECEIVE_POST: [MessageHandler(filters.TEXT & ~filters.COMMAND, receive_post)],
        },
        fallbacks=[CommandHandler("cancel", cancel_rewrite)],
    )
    application.add_handler(rewrite_handler)
    
    # Регистрируем обработчик для кнопок из menu.py (style_ и delete_style_)
    application.add_handler(CallbackQueryHandler(button_callback, pattern="^(style_|delete_style_)"))
    
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("liststyles", list_styles))
    application.add_handler(CallbackQueryHandler(button_callback))
    application.add_handler(new_style_handler)
    
    application.run_polling()


if __name__ == "__main__":
    main()