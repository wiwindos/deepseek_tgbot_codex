# utils.py

import tiktoken
from functools import lru_cache

# Стоимость за 1M токенов (в долларах)
PRICES = {
    "gpt-4": 0.03,  # для сравнения
    "gpt-3.5-turbo": 0.0015,  # для сравнения
    "deepseek-chat": {
        "input": 0.27,  # $0.27 за 1M input tokens
        "output": 1.10  # $1.10 за 1M output tokens
    },
    "deepseek-reasoner": {
        "input": 0.55,  # $0.55 за 1M input tokens
        "output": 2.19  # $2.19 за 1M output tokens
    }
}

@lru_cache(maxsize=2)
def _get_encoding(model):
    """Получение токенизатора с кэшированием"""
    try:
        return tiktoken.encoding_for_model(model)
    except KeyError:
        return tiktoken.get_encoding("cl100k_base")

def num_tokens_from_messages(messages, model="gpt-4"):
    """
    Подсчёт количества токенов во входном сообщении.
    Используется tiktoken (официальный токенизатор от OpenAI).
    
    Args:
        messages: Список сообщений в формате {"role": "...", "content": "..."}
        model: Имя модели для выбора токенизатора
    
    Returns:
        int: Количество токенов
    """
    encoding = _get_encoding(model)
    num_tokens = 0
    for message in messages:
        num_tokens += 4  # стандартное сообщение
        for key, value in message.items():
            num_tokens += len(encoding.encode(value))
    num_tokens += 2  # для завершения
    return num_tokens

def calculate_cost(model, tokens, token_type="input"):
    """
    Расчёт примерной стоимости по числу токенов.
    
    Args:
        model: Имя модели
        tokens: Количество токенов
        token_type: "input" или "output"
    
    Returns:
        float: Стоимость с точностью до 6 знаков
    """
    if not isinstance(tokens, int) or tokens < 0:
        raise ValueError("Tokens must be positive integer")
    
    if model in ["deepseek-chat", "deepseek-reasoner"]:
        try:
            price_per_million = PRICES[model].get(token_type, 0)
            return round((tokens / 1_000_000) * price_per_million, 6)
        except KeyError:
            raise ValueError(f"Unknown model: {model}")
    else:
        # Для других моделей (GPT) оставляем старую логику
        price_per_1k = PRICES.get(model, 0.0015)
        return round((tokens / 1000) * price_per_1k, 6)
