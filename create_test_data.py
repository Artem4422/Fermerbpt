"""
Скрипт для создания тестовой сессии с товарами и заказами
"""
import database
import sqlite3
import sys
from datetime import datetime

# Настройка кодировки для Windows
if sys.platform == 'win32':
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

# ID администратора для создания сессии (можно использовать любой существующий ID)
ADMIN_ID = 1

def create_test_session():
    """Создает тестовую сессию с товарами и заказами"""
    
    print("Создание тестовой сессии...")
    
    # Проверяем/создаем администратора
    conn = sqlite3.connect(database.DB_NAME)
    cursor = conn.cursor()
    
    # Проверяем существование пользователя с ADMIN_ID
    cursor.execute("SELECT user_id FROM users WHERE user_id = ?", (ADMIN_ID,))
    if not cursor.fetchone():
        # Создаем тестового администратора
        cursor.execute("""
            INSERT INTO users (user_id, first_name, username, chat_id, is_bot)
            VALUES (?, ?, ?, ?, 0)
        """, (ADMIN_ID, "Admin", "admin", ADMIN_ID))
        conn.commit()
        print(f"Создан администратор с ID: {ADMIN_ID}")
    
    # Проверяем/создаем запись администратора
    cursor.execute("SELECT user_id FROM admins WHERE user_id = ?", (ADMIN_ID,))
    if not cursor.fetchone():
        cursor.execute("INSERT INTO admins (user_id) VALUES (?)", (ADMIN_ID,))
        conn.commit()
        print(f"Добавлен в администраторы: {ADMIN_ID}")
    
    conn.close()
    
    # 1. Создаем сессию
    session_name = f"Тестовая сессия {datetime.now().strftime('%Y-%m-%d %H:%M')}"
    session_id = database.add_session(session_name, ADMIN_ID)
    
    if not session_id:
        print("Ошибка при создании сессии! Возможно, сессия с таким именем уже существует.")
        # Пробуем с другим именем
        session_name = f"Тестовая сессия {datetime.now().strftime('%Y%m%d%H%M%S')}"
        session_id = database.add_session(session_name, ADMIN_ID)
        if not session_id:
            print("Критическая ошибка при создании сессии!")
            return
    
    print(f"✅ Создана сессия: {session_name} (ID: {session_id})")
    
    # 2. Добавляем товары
    products_data = [
        {"name": "Яблоки", "price": 500.0, "boxes": 100},
        {"name": "Груши", "price": 600.0, "boxes": 80},
        {"name": "Виноград", "price": 800.0, "boxes": 50},
        {"name": "Персики", "price": 700.0, "boxes": 60},
        {"name": "Сливы", "price": 550.0, "boxes": 90},
    ]
    
    product_ids = {}
    for product_data in products_data:
        product_id = database.add_product(
            session_id=session_id,
            product_name=product_data["name"],
            price=product_data["price"],
            boxes_count=product_data["boxes"],
            created_by=ADMIN_ID
        )
        if product_id:
            product_ids[product_data["name"]] = product_id
            print(f"✅ Добавлен товар: {product_data['name']} - {product_data['price']}₽ ({product_data['boxes']} ящиков)")
    
    # 3. Создаем или получаем тестовых пользователей
    conn = sqlite3.connect(database.DB_NAME)
    cursor = conn.cursor()
    
    # Проверяем существующих пользователей или создаем тестовых
    cursor.execute("SELECT user_id FROM users LIMIT 5")
    existing_users = cursor.fetchall()
    
    test_users = []
    if existing_users:
        test_users = [user[0] for user in existing_users[:5]]
        print(f"✅ Используем существующих пользователей: {test_users}")
    else:
        # Создаем тестовых пользователей
        test_user_data = [
            {"user_id": 1001, "first_name": "Иван", "username": "ivan_test"},
            {"user_id": 1002, "first_name": "Мария", "username": "maria_test"},
            {"user_id": 1003, "first_name": "Петр", "username": "petr_test"},
            {"user_id": 1004, "first_name": "Анна", "username": "anna_test"},
            {"user_id": 1005, "first_name": "Сергей", "username": "sergey_test"},
        ]
        
        for user_data in test_user_data:
            try:
                cursor.execute("""
                    INSERT INTO users (user_id, first_name, username, chat_id, is_bot)
                    VALUES (?, ?, ?, ?, 0)
                """, (user_data["user_id"], user_data["first_name"], user_data["username"], user_data["user_id"]))
                test_users.append(user_data["user_id"])
                print(f"✅ Создан тестовый пользователь: {user_data['first_name']} (ID: {user_data['user_id']})")
            except sqlite3.IntegrityError:
                test_users.append(user_data["user_id"])
                print(f"ℹ️ Пользователь {user_data['user_id']} уже существует")
        
        conn.commit()
    
    conn.close()
    
    # 4. Создаем тестовые заказы
    orders_data = [
        {
            "user_id": test_users[0] if test_users else 1001,
            "full_name": "Иван Иванов",
            "phone": "+79001234567",
            "items": [
                {"product_name": "Яблоки", "quantity": 2},
                {"product_name": "Груши", "quantity": 1},
            ],
            "status": "pending"
        },
        {
            "user_id": test_users[1] if len(test_users) > 1 else 1002,
            "full_name": "Мария Петрова",
            "phone": "+79001234568",
            "items": [
                {"product_name": "Виноград", "quantity": 3},
                {"product_name": "Персики", "quantity": 2},
            ],
            "status": "processing"
        },
        {
            "user_id": test_users[2] if len(test_users) > 2 else 1003,
            "full_name": "Петр Сидоров",
            "phone": "+79001234569",
            "items": [
                {"product_name": "Сливы", "quantity": 5},
                {"product_name": "Яблоки", "quantity": 3},
            ],
            "status": "completed"
        },
        {
            "user_id": test_users[0] if test_users else 1001,
            "full_name": "Иван Иванов",
            "phone": "+79001234567",
            "items": [
                {"product_name": "Груши", "quantity": 2},
            ],
            "status": "pending"
        },
        {
            "user_id": test_users[3] if len(test_users) > 3 else 1004,
            "full_name": "Анна Козлова",
            "phone": "+79001234570",
            "items": [
                {"product_name": "Виноград", "quantity": 1},
                {"product_name": "Персики", "quantity": 1},
                {"product_name": "Сливы", "quantity": 2},
            ],
            "status": "pending"
        },
    ]
    
    print("\nСоздание тестовых заказов...")
    created_orders = []
    
    for order_data in orders_data:
        # Формируем список товаров для заказа
        items = []
        for item in order_data["items"]:
            product_id = product_ids.get(item["product_name"])
            if product_id:
                # Получаем цену товара
                product = database.get_product(product_id)
                if product:
                    items.append({
                        "product_id": product_id,
                        "quantity": item["quantity"],
                        "price": product["price"]
                    })
        
        if items:
            # Создаем заказ
            order_id = database.create_order(
                user_id=order_data["user_id"],
                session_id=session_id,
                phone_number=order_data["phone"],
                full_name=order_data["full_name"],
                items=items
            )
            
            if order_id:
                # Обновляем статус заказа
                database.update_order_status(order_id, order_data["status"])
                created_orders.append(order_id)
                
                order = database.get_order(order_id)
                print(f"✅ Создан заказ #{order['order_number']} - {order_data['full_name']} (Статус: {order_data['status']})")
    
    # 5. Активируем торговлю для сессии
    database.set_session_trading_status(session_id, True)
    
    print(f"\n✅ Тестовая сессия создана успешно!")
    print(f"📊 Статистика:")
    print(f"   - Сессия: {session_name}")
    print(f"   - Товаров: {len(product_ids)}")
    print(f"   - Заказов: {len(created_orders)}")
    print(f"   - Торговля: Активна")
    print(f"\n💡 Session ID: {session_id}")


if __name__ == "__main__":
    # Инициализируем БД
    database.init_database()
    
    # Создаем тестовые данные
    create_test_session()
