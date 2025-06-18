import logging
import time
import asyncio
import uuid
import json
import sqlite3
from typing import Dict, Optional

from aiogram import Bot, Dispatcher, types, Router, F
from aiogram.types import Message
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.filters import Command
from aiogram.exceptions import TelegramBadRequest

from openai import AsyncOpenAI
from config import (
    TELEGRAM_BOT_TOKEN,
    OPENAI_API_KEY,
    SECRET_KEYWORD,
    OPENAI_BASE_URL,
    OPENAI_MODEL
)
from database import init_db, save_interaction, get_user_model, set_user_model, DB_PATH
from utils import num_tokens_from_messages, calculate_cost

# Глобальные словари для управления состоянием
active_requests: Dict[int, float] = {}  # Таймстампы активных запросов
authorized_users: Dict[int, bool] = {}  # Кэш авторизованных пользователей

# Таймаут запроса в секундах (5 минут)
REQUEST_TIMEOUT = 300
# Время жизни кэша авторизации в секундах (1 час)
AUTH_CACHE_TTL = 3600

# Настройка клиента OpenAI
client = AsyncOpenAI(
    api_key=OPENAI_API_KEY,
    base_url=OPENAI_BASE_URL
)

# Настройка логгера
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Инициализация бота и диспетчера
bot = Bot(token=TELEGRAM_BOT_TOKEN)
dp = Dispatcher(storage=MemoryStorage())
router = Router()

async def send_long_message(message: Message, text: str, max_length: int = 4096, edit_message=None) -> None:
    """
    Отправляет длинное сообщение частями или редактирует существующее сообщение
    
    Args:
        message: Объект сообщения aiogram
        text: Текст для отправки
        max_length: Максимальная длина части (по умолчанию 4096)
        edit_message: объект сообщения, который нужно отредактировать (aiogram.types.Message)
    """
    parts = [text[x:x + max_length] for x in range(0, len(text), max_length)]
    for i, part in enumerate(parts):
        try:
            if i == 0 and edit_message is not None:
                await edit_message.edit_text(part)
            else:
                await message.reply(part)
        except TelegramBadRequest as e:
            logger.error(f"Failed to send message part: {e}")

@router.message(Command("test_long_message"))
async def test_long_message(message: Message) -> None:
    """
    Тестовая команда для проверки обработки длинных сообщений
    
    Args:
        message: Входящее сообщение
    """
    user_id = message.from_user.id
    model = get_user_model(user_id)
    
    # Генерируем очень длинный тестовый текст (>4000 символов)
    long_text = "Это тестовое длинное сообщение для проверки работы бота.\n" * 100
    
    try:
        if model == "deepseek-reasoner":
            # Для модели с рассуждениями разделяем на части
            reasoning_part = "🧠 Рассуждения:\n\n" + "Здесь будут логические рассуждения модели...\n" * 200
            answer_part = "💡 Ответ:\n\n" + long_text
            
            await send_long_message(message, reasoning_part)
            await send_long_message(message, answer_part)
        else:
            # Для обычной модели просто отправляем длинный текст
            await send_long_message(message, long_text)
    except Exception as e:
        logger.error(f"Error in test_long_message for user {user_id}: {e}")
        await message.reply("⚠️ Произошла ошибка при обработке тестового сообщения")

@router.message(Command("auth"))
async def auth_user(message: Message) -> None:
    """
    Авторизация пользователя
    
    Args:
        message: Входящее сообщение с командой
    """
    user_id = message.from_user.id
    args = message.text.split()
    
    if len(args) != 2:
        await message.reply("Используйте: /auth <секретный_ключ>")
        return
    
    if args[1] != SECRET_KEYWORD:
        await message.reply("Неверный секретный ключ")
        return
    
    try:
        # Проверяем существование таблиц
        with sqlite3.connect(DB_PATH) as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='user_settings'")
            if not cursor.fetchone():
                init_db()
            
            # Обновляем статус авторизации в user_settings
            cursor.execute('''
                INSERT OR REPLACE INTO user_settings (user_id, is_authorized, model_name)
                VALUES (?, 1, 'deepseek-chat')
            ''', (user_id,))
            conn.commit()

        # Сохраняем запрос авторизации
        save_interaction(
            user_id=user_id,
            conversation_id=str(uuid.uuid4()),
            message_type='prompt',
            content='auth_command',
            tokens=0,
            cost=0,
            timestamp=time.time(),
            model_name='system'
        )
        
        # Очищаем возможный старый флаг активного запроса
        active_requests.pop(user_id, None)
        # Обновляем кэш авторизации
        authorized_users[user_id] = True
        await message.reply("✅ Авторизация успешна! Теперь вы можете использовать бота.")
    except Exception as e:
        logger.error(f"Error authorizing user {user_id}: {e}")
        await message.reply("⚠️ Ошибка авторизации. Попробуйте снова или перезапустите бота.")

@router.message(Command("model"))
async def handle_model_command(message: Message):
    await message.reply("Используйте /model_chat или /model_reasoner для выбора модели")

@router.message(Command("model_chat"))
async def set_model_chat(message: Message) -> None:
    """
    Установка модели deepseek-chat для пользователя
    
    Args:
        message: Входящее сообщение с командой
    """
    user_id = message.from_user.id
    
    try:
        # Проверяем авторизацию через get_user_model
        model = get_user_model(user_id)
        if model == "deepseek-chat":
            await message.answer("✅ Модель уже установлена на deepseek-chat")
            return
            
        # Проверяем существование таблиц
        with sqlite3.connect(DB_PATH) as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='interactions'")
            if not cursor.fetchone():
                init_db()
            
        # Обновляем модель пользователя
        set_user_model(user_id, "deepseek-chat")
            
        # Сохраняем лог изменения модели
        save_interaction(
            user_id=user_id,
            conversation_id=str(uuid.uuid4()),
            message_type='system',
            content='model_change_to_chat',
            tokens=0,
            cost=0,
            timestamp=time.time(),
            model_name='deepseek-chat'
        )
        
        # Очищаем контекст
        with sqlite3.connect(DB_PATH) as conn:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM conversation_context WHERE user_id = ?", (user_id,))
            conn.commit()
        
        await message.answer("✅ Модель изменена на deepseek-chat\nКонтекст очищен")
    except Exception as e:
        logger.error(f"Error setting model_chat for user {user_id}: {str(e)}")
        error_details = f"Ошибка: {str(e)}" if str(e) else "Неизвестная ошибка"
        await message.answer(
            f"⚠️ Ошибка при изменении модели\n"
            f"🔹 {error_details}\n"
            f"🔹 Для полного сброса используйте /new"
        )

@router.message(Command("new"))
async def new_conversation(message: Message) -> None:
    """Начать новый диалог
    
    Args:
        message: Входящее сообщение с командой
    """
    user_id = message.from_user.id
    
    try:
        # Проверяем и инициализируем БД перед выполнением
        init_db()
            
        # Сохраняем информацию о новом диалоге
        save_interaction(
            user_id=user_id,
            conversation_id=str(uuid.uuid4()),
            message_type='system',
            content='new_conversation',
            tokens=0,
            cost=0,
            timestamp=time.time(),
            model_name='system'
        )
        
        # Очищаем контекст
        with sqlite3.connect(DB_PATH) as conn:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM conversation_context WHERE user_id = ?", (user_id,))
            conn.commit()
        
        await message.reply("✅ Новый диалог начат. Предыдущий контекст полностью очищен.")
    except Exception as e:
        logger.error(f"Error starting new conversation for user {user_id}: {e}")
        await message.reply("⚠️ Ошибка при очистке контекста")

@router.message(Command("context"))
async def show_context(message: Message) -> None:
    """Показать текущий контекст диалога
    
    Args:
        message: Входящее сообщение с командой
    """
    user_id = message.from_user.id
    
    try:
        # Проверяем авторизацию
        model = get_user_model(user_id)
        if model == "system":  # Неавторизованный пользователь
            await message.reply("❌ Доступ запрещен. Используйте /auth <ключ> для авторизации.")
            return

        # Проверяем существование таблиц
        with sqlite3.connect(DB_PATH) as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='conversation_context'")
            if not cursor.fetchone():
                await message.reply("Контекст пуст.")
                return

        # Получаем текущий conversation_id
        conversation_id = await _get_conversation_id(user_id)
        
        # Сохраняем запрос на показ контекста
        save_interaction(
            user_id=user_id,
            conversation_id=conversation_id,
            message_type='system',
            content='show_context_request',
            tokens=0,
            cost=0,
            timestamp=time.time(),
            model_name='system'
        )

        # Получаем контекст из БД
        context = []
        with sqlite3.connect(DB_PATH) as conn:
            cursor = conn.cursor()
            cursor.execute('''
                SELECT role, content FROM conversation_context
                WHERE user_id = ? AND conversation_id = ?
                ORDER BY timestamp
            ''', (user_id, conversation_id))
            
            for role, content in cursor.fetchall():
                prefix = "👤 Вы: " if role == 'user' else "🤖 Бот: "
                context.append(f"{prefix}{content}")

        if context:
            await send_long_message(message, "\n\n".join(context))
        else:
            await message.reply("Контекст пуст.")
    except Exception as e:
        logger.error(f"Error showing context for user {user_id}: {e}")
        await message.reply("⚠️ Ошибка при получении контекста")

@router.message(Command("model_reasoner"))
async def set_model_reasoner(message: Message) -> None:
    """Установка модели deepseek-reasoner для пользователя
    
    Args:
        message: Входящее сообщение с командой
    """
    user_id = message.from_user.id
    
    try:
        # Проверяем авторизацию через get_user_model
        model = get_user_model(user_id)
        if model == "deepseek-reasoner":
            await message.reply("✅ Модель уже установлена на deepseek-reasoner")
            return
            
        # Проверяем существование таблиц
        with sqlite3.connect(DB_PATH) as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='interactions'")
            if not cursor.fetchone():
                init_db()
            
        # Обновляем модель пользователя
        set_user_model(user_id, "deepseek-reasoner")
            
        # Сохраняем лог изменения модели
        save_interaction(
            user_id=user_id,
            conversation_id=str(uuid.uuid4()),
            message_type='system',
            content='model_change_to_reasoner',
            tokens=0,
            cost=0,
            timestamp=time.time(),
            model_name='deepseek-reasoner'
        )
        
        # Очищаем контекст
        with sqlite3.connect(DB_PATH) as conn:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM conversation_context WHERE user_id = ?", (user_id,))
            conn.commit()
        
        await message.reply(
            "✅ Модель изменена на deepseek-reasoner\n"
            "🔹 Контекст очищен\n"
            "🔹 Теперь будет использоваться Chain-of-Thought подход"
        )
    except Exception as e:
        logger.error(f"Error setting model_reasoner for user {user_id}: {str(e)}")
        error_details = f"Ошибка: {str(e)}" if str(e) else "Неизвестная ошибка"
        await message.reply(
            f"⚠️ Ошибка при изменении модели\n"
            f"🔹 {error_details}\n"
            f"🔹 Для полного сброса используйте /new"
        )

async def _get_conversation_id(user_id: int) -> str:
    """Internal helper: Returns current conversation ID or creates new one"""
    if not isinstance(user_id, int):
        raise ValueError("user_id must be integer")
    
    conn = None
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        
        # Check if interactions table exists with required columns
        cursor.execute("PRAGMA table_info(interactions)")
        columns = [col[1] for col in cursor.fetchall()]
        required_columns = {'user_id', 'conversation_id', 'timestamp'}
        
        if not required_columns.issubset(columns):
            return str(uuid.uuid4())
            
        cursor.execute('''
            SELECT conversation_id FROM interactions 
            WHERE user_id = ? 
            ORDER BY timestamp DESC 
            LIMIT 1
        ''', (user_id,))
        result = cursor.fetchone()
    except sqlite3.Error as e:
        logging.error(f"Database error in _get_conversation_id: {e}")
        return str(uuid.uuid4())
    finally:
        if conn:
            conn.close()
    return result[0] if result else str(uuid.uuid4())

@router.message()
async def handle_message(message: Message):
    user_id = message.from_user.id
    
    # Проверяем кэш авторизации
    if user_id in authorized_users:
        if not authorized_users[user_id]:
            await message.reply("❌ Доступ запрещен. Используйте /auth <ключ> для авторизации.")
            return
    else:
        try:
            # Проверяем существование таблицы user_settings
            with sqlite3.connect(DB_PATH) as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='user_settings'")
                if not cursor.fetchone():
                    init_db()
                
                # Проверяем авторизацию
                cursor.execute('SELECT is_authorized FROM user_settings WHERE user_id = ?', (user_id,))
                result = cursor.fetchone()
                
            if not result or not result[0]:
                authorized_users[user_id] = False
                await message.reply("❌ Доступ запрещен. Используйте /auth <ключ> для авторизации.")
                return
            else:
                authorized_users[user_id] = True
        except Exception as e:
            logger.error(f"Error checking authorization for user {user_id}: {e}")
            await message.reply("⚠️ Ошибка проверки авторизации. Попробуйте снова.")
            return
    
    # Проверяем есть ли активный запрос для этого пользователя
    last_request_time = active_requests.get(user_id)
    if last_request_time:
        if time.time() - last_request_time < REQUEST_TIMEOUT:
            await message.reply("Ожидайте ответа, после этого попробуйте еще раз.")
            return
        else:
            # Сбрасываем зависший запрос
            active_requests.pop(user_id, None)
        
    # Пропускаем команды и пустые сообщения
    if not message.text or message.text.startswith('/'):
        return
        
    # Устанавливаем флаг активного запроса с timestamp
    active_requests[user_id] = time.time()
    
    try:
        user_input = message.text.strip()
        if not user_input:
            await message.reply("Сообщение не может быть пустым")
            return
        # Сообщаем пользователю, что запрос принят
        wait_msg = await message.reply("Ваш запрос принят, ожидайте ответ!")
    except Exception as e:
        logging.error(f"Error processing message: {e}")
        await message.reply("Произошла ошибка при обработке сообщения")
        active_requests.pop(user_id, None)  # Снимаем блокировку при ошибке
        return
    
        
    prompt = user_input.strip()
    user_id = message.from_user.id
    conversation_id = await _get_conversation_id(user_id)
    if not prompt:  # Проверяем, что промпт не пустой
        await message.reply("Пожалуйста, введите запрос после секретного слова")
        return
        
    user_id = message.from_user.id
    username = message.from_user.username or "unknown"

    model = get_user_model(user_id)
    
    # Получаем историю диалога (последние 10 сообщений)
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    # Проверяем существование таблицы conversation_context
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='conversation_context'")
    if not cursor.fetchone():
        history = []
    else:
        cursor.execute('''
            SELECT role, content FROM conversation_context
            WHERE user_id = ? AND conversation_id = ?
            ORDER BY timestamp ASC
            LIMIT 10
        ''', (user_id, conversation_id))
        history = [{"role": row[0], "content": row[1]} for row in cursor.fetchall()]
    conn.close()
    
    # Для deepseek-reasoner используем только Q&A пары (без reasoning)
    if model == "deepseek-reasoner":
        messages = []
        # Фильтруем только user/assistant сообщения (исключая reasoning)
        for msg in history:
            if msg["role"] == "user":
                # Добавляем user сообщение только если предыдущее было assistant или список пуст
                if not messages or messages[-1]["role"] == "assistant":
                    messages.append({"role": msg["role"], "content": msg["content"]})
            elif msg["role"] == "assistant":
                content = msg["content"]
                # Если это был ответ reasoner, извлекаем только answer часть
                if content.startswith('{"reasoning"'):
                    try:
                        content = json.loads(content)["answer"]
                    except:
                        content = content.split('"answer":')[1].split('"')[1]
                # Добавляем assistant сообщение только если перед ним есть user сообщение
                if messages and messages[-1]["role"] == "user":
                    messages.append({"role": msg["role"], "content": content})
        
        # Убедимся, что первый message - user (если список пуст)
        if not messages:
            messages.append({"role": "user", "content": prompt})
        # Если последнее сообщение - assistant, добавляем новый user prompt
        elif messages[-1]["role"] == "assistant":
            messages.append({"role": "user", "content": prompt})
        # Если последнее сообщение - user, заменяем его на новый prompt
        else:
            messages[-1]["content"] = prompt
    else:
        # Для deepseek-chat используем полную историю
        messages = history + [{"role": "user", "content": prompt}]
    tokens_in = num_tokens_from_messages(messages, model=model)

    start_time = time.time()
    reply_text = ""
    sent_message = None
    tokens_out = 0
    
    # Инициализация буфера
    accumulated_text = ""
    last_sent_text = ""
    last_update_time = 0
    
    try:
        stream = await client.chat.completions.create(
            model=model,
            messages=messages,
            temperature=0.7,
            stream=True
        )
        
        reasoning_text = ""
        answer_text = ""
        tokens_out = 0

        # Просто накапливаем весь ответ (и рассуждения, если есть)
        async for chunk in stream:
            # Обработка reasoning для reasoner модели
            if model == "deepseek-reasoner" and hasattr(chunk.choices[0].delta, 'reasoning_content'):
                reasoning_text += chunk.choices[0].delta.reasoning_content or ""
                tokens_out += 1

            # Обработка основного ответа
            if hasattr(chunk.choices[0].delta, 'content') and chunk.choices[0].delta.content:
                answer_text += chunk.choices[0].delta.content
                tokens_out += 1

        # После завершения стрима финальный ответ заменяет сообщение "Ваш запрос принят"
        if answer_text.strip():
            if model == "deepseek-reasoner":
                await send_long_message(message, f"\U0001F9E0 Рассуждения:\n\n{reasoning_text.strip()}\n\n\U0001F4A1 Ответ:\n\n{answer_text.strip()}", edit_message=wait_msg)
            else:
                await send_long_message(message, answer_text.strip(), edit_message=wait_msg)

    except Exception as e:
        await message.reply(f"Ошибка при обращении к GPT:\n\n{e}")
        return
    finally:
        # Всегда снимаем блокировку после завершения обработки
        active_requests.pop(user_id, None)

    # Фиксируем время окончания генерации ответа
    end_time = time.time()

    # Рассчитываем стоимость отдельно для промпта и ответа
    prompt_cost = calculate_cost(model=model, tokens=tokens_in, token_type="input")
    response_cost = calculate_cost(model=model, tokens=tokens_out, token_type="output")
    total_cost = round(prompt_cost + response_cost, 6)

    # Сохраняем промпт
    save_interaction(
        user_id=user_id,
        conversation_id=conversation_id,
        message_type='prompt',
        content=prompt,
        tokens=tokens_in,
        cost=prompt_cost,
        timestamp=start_time,
        model_name=model
    )
    
    # Сохраняем ответ
    save_interaction(
        user_id=user_id,
        conversation_id=conversation_id,
        message_type='response',
        content=answer_text if model != "deepseek-reasoner" else json.dumps({
            "reasoning": reasoning_text.strip(),
            "answer": answer_text.strip()
        }),
        tokens=tokens_out,
        cost=response_cost,
        timestamp=end_time,
        model_name=model
    )
    
    # Сохраняем в контекст
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    # Проверяем существование таблицы conversation_context
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='conversation_context'")
    if cursor.fetchone():
        cursor.execute('''
            INSERT INTO conversation_context (user_id, conversation_id, role, content, timestamp)
            VALUES (?, ?, ?, ?, ?)
        ''', (user_id, conversation_id, 'user', prompt, start_time))
        
        cursor.execute('''
            INSERT INTO conversation_context (user_id, conversation_id, role, content, timestamp)
            VALUES (?, ?, ?, ?, ?)
        ''', (user_id, conversation_id, 'assistant', answer_text, end_time))
        conn.commit()
    conn.close()

async def main():
    # Initialize database before starting bot
    try:
        init_db()
        logging.info("Database initialized successfully")
    except Exception as e:
        logging.error(f"Failed to initialize database: {e}")
        raise
    
    dp.include_router(router)
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
