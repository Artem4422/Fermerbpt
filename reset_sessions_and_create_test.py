"""Удаляет все сессии и создаёт одну тестовую с товарами."""
import sqlite3
import database

DB_NAME = database.DB_NAME
CREATED_BY = 806966850  # админ/менеджер из проекта

def main():
    database.init_database()
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("PRAGMA foreign_keys = OFF")

    cursor.execute("DELETE FROM order_items")
    cursor.execute("DELETE FROM orders")
    cursor.execute("DELETE FROM user_session_limits")
    cursor.execute("DELETE FROM products")
    cursor.execute("DELETE FROM sessions")
    conn.commit()
    cursor.execute("PRAGMA foreign_keys = ON")
    conn.close()
    print("Все сессии и связанные данные удалены.")

    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute("SELECT user_id FROM users WHERE user_id = ?", (CREATED_BY,))
    if not c.fetchone():
        c.execute("SELECT user_id FROM admins LIMIT 1")
        row = c.fetchone()
        created_by = row[0] if row else None
        if not created_by:
            c.execute("SELECT user_id FROM users LIMIT 1")
            created_by = (c.fetchone() or [1])[0]
    else:
        created_by = CREATED_BY
    conn.close()

    session_id = database.add_session("Тестовая сессия", created_by)
    if not session_id:
        print("Ошибка: не удалось создать сессию.")
        return

    # Товары как в create_test_data
    products_data = [
        {"name": "Яблоки", "price": 500.0, "boxes": 100},
        {"name": "Груши", "price": 600.0, "boxes": 80},
        {"name": "Виноград", "price": 800.0, "boxes": 50},
        {"name": "Персики", "price": 700.0, "boxes": 60},
        {"name": "Сливы", "price": 550.0, "boxes": 90},
    ]
    for p in products_data:
        database.add_product(
            session_id=session_id,
            product_name=p["name"],
            price=p["price"],
            boxes_count=p["boxes"],
            created_by=created_by,
        )
    database.set_session_trading_status(session_id, True)
    print(f"Создана сессия «Тестовая сессия» (id={session_id}) с торговлей, добавлено товаров: {len(products_data)}.")

if __name__ == "__main__":
    main()
