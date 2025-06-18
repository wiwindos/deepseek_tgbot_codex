# database.py

import sqlite3
import logging
import os
from datetime import datetime

DB_FOLDER = os.getenv("DB_FOLDER", "bd")
DB_NAME = "chatgpt_telegram_log.db"
DB_PATH = os.path.join(DB_FOLDER, DB_NAME)

if not os.path.exists(DB_FOLDER):
    os.makedirs(DB_FOLDER)

def _execute_sql(conn, sql, params=None):
    """Вспомогательная функция для выполнения SQL запросов"""
    try:
        cursor = conn.cursor()
        cursor.execute(sql, params or ())
        conn.commit()
        return cursor
    except sqlite3.Error as e:
        logging.error(f"SQL execution error: {e}")
        raise

def init_db():
    """Инициализация базы данных с таблицами и индексами"""
    with sqlite3.connect(DB_PATH) as conn:
        try:
            # Создаем таблицы
            tables = [
                '''
                CREATE TABLE IF NOT EXISTS user_settings (
                    user_id INTEGER PRIMARY KEY,
                    model_name TEXT NOT NULL DEFAULT 'deepseek-chat',
                    is_authorized INTEGER NOT NULL DEFAULT 0,
                    created_at REAL DEFAULT (strftime('%s', 'now'))
                )
                ''',
                '''
                CREATE TABLE IF NOT EXISTS interactions (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER NOT NULL,
                    conversation_id TEXT NOT NULL,
                    message_type TEXT NOT NULL CHECK (message_type IN ('prompt', 'response', 'system')),
                    content TEXT NOT NULL,
                    tokens INTEGER NOT NULL CHECK (tokens >= 0),
                    cost REAL NOT NULL CHECK (cost >= 0),
                    timestamp REAL NOT NULL,
                    model_name TEXT NOT NULL,
                    FOREIGN KEY(user_id) REFERENCES user_settings(user_id) ON DELETE CASCADE
                )
                ''',
                '''
                CREATE TABLE IF NOT EXISTS conversation_context (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER NOT NULL,
                    conversation_id TEXT NOT NULL,
                    role TEXT NOT NULL CHECK (role IN ('user', 'assistant')),
                    content TEXT NOT NULL,
                    timestamp REAL NOT NULL,
                    FOREIGN KEY(user_id) REFERENCES user_settings(user_id) ON DELETE CASCADE
                )
                '''
            ]

            # Создаем индексы
            indexes = [
                'CREATE INDEX IF NOT EXISTS idx_interactions_user ON interactions(user_id)',
                'CREATE INDEX IF NOT EXISTS idx_interactions_conversation ON interactions(conversation_id)',
                'CREATE INDEX IF NOT EXISTS idx_interactions_timestamp ON interactions(timestamp)',
                'CREATE INDEX IF NOT EXISTS idx_context_user_conversation ON conversation_context(user_id, conversation_id)',
                'CREATE INDEX IF NOT EXISTS idx_context_timestamp ON conversation_context(timestamp)'
            ]

            for table_sql in tables:
                _execute_sql(conn, table_sql)
            
            for index_sql in indexes:
                _execute_sql(conn, index_sql)

        except sqlite3.Error as e:
            logging.error(f"Database initialization error: {e}")
            raise

def get_user_model(user_id):
    """Получение модели пользователя с обработкой ошибок"""
    with sqlite3.connect(DB_PATH) as conn:
        try:
            cursor = _execute_sql(conn, 
                "SELECT name FROM sqlite_master WHERE type='table' AND name='user_settings'")
            if not cursor.fetchone():
                return 'deepseek-chat'
            
            cursor = _execute_sql(conn,
                'SELECT model_name FROM user_settings WHERE user_id = ?', (user_id,))
            result = cursor.fetchone()
            return result[0] if result else 'deepseek-chat'
        except sqlite3.Error as e:
            logging.error(f"Error getting user model: {e}")
            return 'deepseek-chat'

def set_user_model(user_id, model_name):
    """Установка модели пользователя"""
    with sqlite3.connect(DB_PATH) as conn:
        try:
            # Инициализируем БД если нужно
            init_db()
            
            # Простая и надежная вставка/обновление
            _execute_sql(conn, '''
                INSERT OR REPLACE INTO user_settings 
                (user_id, model_name, is_authorized, created_at)
                VALUES (?, ?, COALESCE(
                    (SELECT is_authorized FROM user_settings WHERE user_id = ?), 
                    0
                ), 
                COALESCE(
                    (SELECT created_at FROM user_settings WHERE user_id = ?),
                    strftime('%s', 'now')
                ))
            ''', (user_id, model_name, user_id, user_id))
        except sqlite3.Error as e:
            logging.error(f"Error setting user model: {e}")
            raise

def save_interaction(user_id, conversation_id, message_type, content, 
                    tokens, cost, timestamp, model_name):
    """Сохранение взаимодействия с пользователем"""
    with sqlite3.connect(DB_PATH) as conn:
        try:
            _execute_sql(conn, '''
                INSERT INTO interactions (
                    user_id, conversation_id, message_type, content,
                    tokens, cost, timestamp, model_name
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                user_id, conversation_id, message_type, content,
                tokens, cost, timestamp, model_name
            ))
        except sqlite3.Error as e:
            logging.error(f"Error saving interaction: {e}")
            raise
