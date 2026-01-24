import sqlite3
import os

DB_NAME = "bot_database.db"

def clear_users():
    """Очищает таблицу users от всех записей"""
    if not os.path.exists(DB_NAME):
        print(f"База данных {DB_NAME} не найдена!")
        return
    
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    
    try:
        # Подсчитываем количество пользователей перед удалением
        cursor.execute("SELECT COUNT(*) FROM users")
        count = cursor.fetchone()[0]
        
        # Удаляем всех пользователей
        cursor.execute("DELETE FROM users")
        
        conn.commit()
        print(f"Успешно удалено {count} пользователей из базы данных.")
    except Exception as e:
        print(f"Ошибка при удалении пользователей: {e}")
        conn.rollback()
    finally:
        conn.close()

if __name__ == '__main__':
    clear_users()
