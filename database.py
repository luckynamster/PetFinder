import sqlite3
from datetime import datetime


def initialize_database():
    conn = sqlite3.connect('database.db')
    cursor = conn.cursor()

    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            chat_id INTEGER UNIQUE NOT NULL,
            username TEXT,
            registration_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')

    cursor.execute('''
        CREATE TABLE IF NOT EXISTS requests (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            request_type TEXT CHECK(request_type IN ('found', 'lost')),
            photo_data BLOB NOT NULL,
            breed TEXT,
            category TEXT,
            gender TEXT CHECK(gender IN ('самец', 'самка', 'неизвестно')),
            size TEXT CHECK(size IN ('маленький', 'средний', 'большой')),
            hair TEXT CHECK(hair IN ('короткая', 'длинная', 'нет')),
            city TEXT NOT NULL,
            chip_number TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            is_active INTEGER DEFAULT 1 CHECK(is_active IN (0, 1)), 
            FOREIGN KEY(user_id) REFERENCES users(id)
        )
    ''')
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS notifications (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            source_request INTEGER,
            matched_request INTEGER,
            similarity REAL,
            notified_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            UNIQUE(source_request, matched_request),  -- Добавляем уникальность
            FOREIGN KEY(source_request) REFERENCES requests(id),
            FOREIGN KEY(matched_request) REFERENCES requests(id)
        )
    ''')
    conn.commit()
    conn.close()
    print(f"[{datetime.now()}] База данных инициализирована")
initialize_database()
