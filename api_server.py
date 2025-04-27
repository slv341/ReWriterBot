import os
import logging
from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from openai import OpenAI

# Настройка логирования
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Загружаем переменные из .env
load_dotenv()
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

# Проверяем наличие API-ключа OpenAI
if not OPENAI_API_KEY:
    raise ValueError("OPENAI_API_KEY not found in .env file")

# Инициализируем FastAPI приложение
app = FastAPI()

# Инициализируем клиент OpenAI
openai_client = OpenAI(api_key=OPENAI_API_KEY)

# Модель для входных данных
class RewriteRequest(BaseModel):
    system_prompt: str
    example_text: str
    post_text: str

@app.post("/rewrite")
async def rewrite_text(request: RewriteRequest):
    """Эндпоинт для рерайта текста через OpenAI API."""
    try:
        # Формируем сообщения для OpenAI
        messages = [
            {
                "role": "system",
                "content": (
                    f"{request.system_prompt}\n\n"
                    f"Here is an example of the style:\n{request.example_text}"
                )
            },
            {
                "role": "user",
                "content": f"{request.post_text}"
            }
        ]

        # Отправляем запрос к OpenAI
        response = openai_client.chat.completions.create(
            model="gpt-4o-mini",
            messages=messages,
            max_tokens=750,
            temperature=0.7
        )

        # Извлекаем переписанный текст
        rewritten_text = response.choices[0].message.content.strip()
        logger.info(f"Текст успешно переписан через OpenAI: {rewritten_text[:100]}...")

        return {"rewritten_text": rewritten_text}

    except Exception as e:
        logger.error(f"Ошибка при вызове OpenAI API: {e}")
        raise HTTPException(status_code=500, detail=f"Ошибка при рерайте текста: {e}")