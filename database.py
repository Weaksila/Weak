import sqlite3
import datetime
from contextlib import contextmanager

DB_NAME = "gym_bot.db"

@contextmanager
def get_db_connection():
    conn = sqlite3.connect(DB_NAME)
    try:
        yield conn
    finally:
        conn.close()

def init_db():
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY,
                telegram_id INTEGER UNIQUE,
                height REAL DEFAULT 0
            )
        """)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS workouts (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                date TEXT,
                exercise TEXT,
                sets INTEGER,
                reps INTEGER,
                weight REAL,
                FOREIGN KEY (user_id) REFERENCES users(id)
            )
        """)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS nutrition (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                date TEXT,
                food_item TEXT,
                protein REAL,
                fat REAL,
                carbs REAL,
                FOREIGN KEY (user_id) REFERENCES users(id)
            )
        """)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS weight_history (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                date TEXT,
                weight REAL,
                FOREIGN KEY (user_id) REFERENCES users(id)
            )
        """)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS water_intake (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                date TEXT,
                amount_ml INTEGER,
                FOREIGN KEY (user_id) REFERENCES users(id)
            )
        """)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS ai_chat_history (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                timestamp TEXT,
                role TEXT,
                content TEXT,
                FOREIGN KEY (user_id) REFERENCES users(id)
            )
        """)
        conn.commit()

def add_user(telegram_id):
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("INSERT OR IGNORE INTO users (telegram_id) VALUES (?)", (telegram_id,))
        conn.commit()

def update_user_height(telegram_id, height):
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("UPDATE users SET height = ? WHERE telegram_id = ?", (height, telegram_id))
        conn.commit()

def get_user_height(telegram_id):
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT height FROM users WHERE telegram_id = ?", (telegram_id,))
        height = cursor.fetchone()
        return height[0] if height else None

def add_weight(user_id, date, weight):
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("INSERT INTO weight_history (user_id, date, weight) VALUES (?, ?, ?)",
                       (user_id, date, weight))
        conn.commit()

def get_user_id(telegram_id):
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT id FROM users WHERE telegram_id = ?", (telegram_id,))
        user_id = cursor.fetchone()
        return user_id[0] if user_id else None

def get_weight_history(user_id, limit=None):
    with get_db_connection() as conn:
        cursor = conn.cursor()
        query = "SELECT date, weight FROM weight_history WHERE user_id = ? ORDER BY date ASC"
        if limit: query += f" LIMIT {limit}"
        cursor.execute(query, (user_id,))
        return cursor.fetchall()

def add_water_intake(user_id, date, amount_ml):
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("INSERT INTO water_intake (user_id, date, amount_ml) VALUES (?, ?, ?)", (user_id, date, amount_ml))
        conn.commit()

def add_ai_message(user_id, role, content):
    with get_db_connection() as conn:
        cursor = conn.cursor()
        timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        cursor.execute("INSERT INTO ai_chat_history (user_id, timestamp, role, content) VALUES (?, ?, ?, ?)",
                       (user_id, timestamp, role, content))
        conn.commit()

def get_ai_chat_history(user_id, limit=10):
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT role, content FROM ai_chat_history WHERE user_id = ? ORDER BY timestamp DESC LIMIT ?", (user_id, limit))
        history = cursor.fetchall()
        return history[::-1]

def add_workout(user_id, date, exercise, sets, reps, weight):
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("INSERT INTO workouts (user_id, date, exercise, sets, reps, weight) VALUES (?, ?, ?, ?, ?, ?)",
                       (user_id, date, exercise, sets, reps, weight))
        conn.commit()

def add_nutrition(user_id, date, food_item, protein, fat, carbs):
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("INSERT INTO nutrition (user_id, date, food_item, protein, fat, carbs) VALUES (?, ?, ?, ?, ?, ?)",
                       (user_id, date, food_item, protein, fat, carbs))
        conn.commit()

def get_workouts(user_id, date):
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT exercise, sets, reps, weight FROM workouts WHERE user_id = ? AND date = ?", (user_id, date))
        return cursor.fetchall()

def get_nutrition(user_id, date):
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT food_item, protein, fat, carbs FROM nutrition WHERE user_id = ? AND date = ?", (user_id, date))
        return cursor.fetchall()

def get_daily_water_intake(user_id, date):
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT SUM(amount_ml) FROM water_intake WHERE user_id = ? AND date = ?", (user_id, date))
        total_ml = cursor.fetchone()[0]
        return total_ml if total_ml else 0

def add_reminder(user_id, time, message):
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("INSERT INTO reminders (user_id, time, message) VALUES (?, ?, ?)", (user_id, time, message))
        conn.commit()

def get_reminders(user_id):
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT time, message FROM reminders WHERE user_id = ?", (user_id,))
        return cursor.fetchall()
