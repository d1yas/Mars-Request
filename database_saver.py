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
            status TEXT NULL DEFAULT "Javob kutilmoqda",
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
    data = datetime.now().strftime("%Y-%m-%d")
    cursor.execute('''
        INSERT INTO sorov_table (user_id, name, time, guruxlar, filial, sabab, data)
        VALUES (?, ?, ?, ?, ?, ?, ?)
    ''', (user_id, name, time, guruxlar, filial, sabab, data))
    conn.commit()
    last_id = cursor.lastrowid
    conn.close()
    return last_id


def update_status(request_id, new_status):
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute('''
        UPDATE sorov_table
        SET status = ?
        WHERE id = ?
    ''', (new_status, request_id))
    conn.commit()
    conn.close()

def save_request_to_history(request_id):
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute('''
        SELECT user_id, name, time, guruxlar, status, filial, sabab, data
        FROM sorov_table
        WHERE id = ?
    ''', (request_id,))
    request = cursor.fetchone()

    if request:
        user_id, name, time, guruxlar, status, filial, sabab, data = request
        cursor.execute('''
            INSERT INTO history_sorov (user_id, name, time, guruxlar, status, filial, sabab, data)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        ''', (user_id, name, time, guruxlar, status, filial, sabab, data))
        cursor.execute('DELETE FROM sorov_table WHERE id = ?', (request_id,))

    conn.commit()
    conn.close()

def get_user_data(request_id):
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute('''
        SELECT name, time, guruxlar, filial, sabab, data, id, status
        FROM sorov_table
        WHERE id = ?
    ''', (request_id,))
    result = cursor.fetchone()
    conn.close()

    if result:
        name, time, guruxlar, filial, sabab, data, id, status = result
        return {
            "name": name,
            "time": time,
            "guruxlar": guruxlar,
            "filial": filial,
            "sabab": sabab,
            "data": data,
            "id": id,
            "status": status
        }
    return None

def get_all_pending_requests():
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute('''
        SELECT id, user_id, name, time, guruxlar, filial, sabab, data
        FROM sorov_table
        WHERE status = "Javob kutilmoqda"
    ''')
    results = cursor.fetchall()
    conn.close()
    
    pending_requests = []
    for result in results:
        id, user_id, name, time, guruxlar, filial, sabab, data = result
        pending_requests.append({
            "id": id,
            "user_id": user_id,
            "name": name,
            "time": time,
            "guruxlar": guruxlar,
            "filial": filial,
            "sabab": sabab,
            "data": data
        })
    
    return pending_requests