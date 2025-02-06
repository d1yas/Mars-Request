import sqlite3
from datetime import datetime

DB_NAME = "user_data.db"

def create_table():
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()

    cursor.execute('''
        CREATE TABLE IF NOT EXISTS sorov_table (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NULL,
            time TEXT NULL,
            guruxlar TEXT NULL,
            status TEXT NULL DEFAULT "Ожидание ответа",
            filial TEXT NULL,
            user_id INTEGER NOT NULL,
            sabab TEXT NULL,
            data TEXT NULL
        )
    ''')

    cursor.execute('''
        CREATE TABLE IF NOT EXISTS history_sorov (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NULL,
            time TEXT NULL,
            guruxlar TEXT NULL,
            status TEXT NULL,
            filial TEXT NULL,
            user_id INTEGER NOT NULL,
            sabab TEXT NULL,
            data TEXT NULL
        )
    ''')

    conn.commit()
    conn.close()

create_table()

def save_request_sorov_table(user_id, name, time, guruxlar, filial, sabab):
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    data = datetime.now().strftime("%Y-%m-%d")  # Hozirgi sanani olish
    cursor.execute('''
        INSERT INTO sorov_table (user_id, name, time, guruxlar, filial, sabab, data)
        VALUES (?, ?, ?, ?, ?, ?, ?)
    ''', (user_id, name, time, guruxlar, filial, sabab, data))
    conn.commit()
    conn.close()

def update_status(user_id, new_status):
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute('''
        UPDATE sorov_table
        SET status = ?
        WHERE user_id = ?
    ''', (new_status, user_id))
    conn.commit()
    conn.close()

def save_request_to_history(user_id):
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute('''
        SELECT name, time, guruxlar, status, filial, sabab, data
        FROM sorov_table
        WHERE user_id = ?
    ''', (user_id,))
    request = cursor.fetchone()

    if request:
        name, time, guruxlar, status, filial, sabab, data = request
        cursor.execute('''
            INSERT INTO history_sorov (user_id, name, time, guruxlar, status, filial, sabab, data)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        ''', (user_id, name, time, guruxlar, status, filial, sabab, data))
        cursor.execute('DELETE FROM sorov_table WHERE user_id = ?', (user_id,))

    conn.commit()
    conn.close()

def get_user_data(user_id):
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute('''
        SELECT name, time, guruxlar, filial, sabab, data
        FROM sorov_table
        WHERE user_id = ?
    ''', (user_id,))
    result = cursor.fetchone()
    conn.close()

    if result:
        name, time, guruxlar, filial, sabab, data = result
        return {
            "name": name,
            "time": time,
            "guruxlar": guruxlar,
            "filial": filial,
            "sabab": sabab,
            "data": data
        }
    return None


