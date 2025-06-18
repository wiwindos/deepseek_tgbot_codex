# 🤖 Telegram GPT Bot (DeepSeek + SQLite + Aiogram)

[![Python Version](https://img.shields.io/badge/python-3.10%2B-blue)](https://www.python.org/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Aiogram](https://img.shields.io/badge/Aiogram-3.x-blue)](https://docs.aiogram.dev/)

A feature-rich Telegram bot that provides access to GPT models (DeepSeek, OpenRouter, Together AI, etc.) with conversation logging, token tracking, and cost calculation.

## ✨ Features

- **Secure Access**: Restricted by secret keyword
- **Multiple Models**: Supports DeepSeek, OpenRouter, Together AI and other OpenAI-compatible providers
- **Conversation Logging**: All interactions stored in SQLite
- **Token Tracking**: Input/output tokens counting
- **Cost Calculation**: Real-time cost estimation
- **Context Management**: Conversation history support
- **Long Message Handling**: Automatic splitting of long responses
- **Two Model Types**:
  - `deepseek-chat`: Standard chat model
  - `deepseek-reasoner`: Chain-of-Thought reasoning model

## 🚀 Quick Start

### Prerequisites
- Python 3.10+
- Telegram Bot Token
- OpenAI-compatible API key

### Installation
1. Clone the repository:
```bash
git clone https://github.com/yourusername/telegram-gpt-bot.git
cd telegram-gpt-bot
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

### Configuration
Edit `config.py` with your credentials:
```python
TELEGRAM_BOT_TOKEN = "your_bot_token"
OPENAI_API_KEY = "your_api_key"
SECRET_KEYWORD = "your_secret_word"  # Access control keyword

# Default model (deepseek-chat or deepseek-reasoner)
OPENAI_MODEL = "deepseek-chat"

# Provider URL (DeepSeek, OpenRouter, Together AI, etc.)
OPENAI_BASE_URL = "https://api.deepseek.com/v1"
```

### Running the Bot
```bash
python main.py
```

For v12 version:
```bash
python v12/main.py
```

## 🛠 Commands

| Command | Description |
|---------|-------------|
| `/auth <secret>` | Authorize with secret keyword |
| `/model_chat` | Switch to standard chat model |
| `/model_reasoner` | Switch to reasoning model |
| `/new` | Start new conversation (clear context) |
| `/context` | Show current conversation context |
| `/test_long_message` | Test long message handling |

## 💻 Usage Example
```
/ auth your_secret_word
[Bot] ✅ Authorization successful! Now you can use the bot.

your_secret_word Explain quantum computing
[Bot] Quantum computing is a type of computation...
```

## 🗃 Database Structure
The bot uses SQLite (`chatgpt_telegram_log.db`) with these tables:

### `interactions`
| Column | Type | Description |
|--------|------|-------------|
| user_id | INTEGER | Telegram user ID |
| conversation_id | TEXT | Conversation identifier |
| message_type | TEXT | 'prompt', 'response' or 'system' |
| content | TEXT | Message content |
| tokens | INTEGER | Token count |
| cost | REAL | Estimated cost in USD |
| timestamp | REAL | Unix timestamp |
| model_name | TEXT | Model used |

### `user_settings`
| Column | Type | Description |
|--------|------|-------------|
| user_id | INTEGER | Telegram user ID (PK) |
| model_name | TEXT | Selected model |
| is_authorized | INTEGER | Authorization status |
| created_at | REAL | Account creation time |

### `conversation_context`
| Column | Type | Description |
|--------|------|-------------|
| user_id | INTEGER | Telegram user ID |
| conversation_id | TEXT | Conversation identifier |
| role | TEXT | 'user' or 'assistant' |
| content | TEXT | Message content |
| timestamp | REAL | Unix timestamp |

## 🌟 Advanced Features

### Multiple Model Support
Configure different providers in `config.py`:

```python
# DeepSeek
OPENAI_MODEL = "deepseek-chat"
OPENAI_BASE_URL = "https://api.deepseek.com/v1"

# OpenRouter
OPENAI_MODEL = "mistralai/Mixtral-8x7B-Instruct-v0.1"
OPENAI_BASE_URL = "https://openrouter.ai/api/v1"

# Together AI
OPENAI_MODEL = "togethercomputer/llama-2-70b-chat"
OPENAI_BASE_URL = "https://api.together.xyz/v1"
```

### Cost Calculation
The bot calculates costs based on:

| Model | Input (per 1M) | Output (per 1M) |
|-------|---------------|----------------|
| deepseek-chat | $0.27 | $1.10 |
| deepseek-reasoner | $0.55 | $2.19 |

## 📜 License
MIT License - see [LICENSE](LICENSE) for details.
