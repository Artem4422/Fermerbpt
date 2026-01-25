"""
Скрипт для создания 100 тестовых заказов в сессии
"""
import database
import sqlite3
import sys
import random
from datetime import datetime, timedelta

# Настройка кодировки для Windows
if sys.platform == 'win32':
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

# ID администратора
ADMIN_ID = 1

def create_100_orders(session_id: int = None):
    """Создает 100 тестовых заказов в указанной сессии или создает новую"""
    
    print("Создание 100 тестовых заказов...")
    
    # Если сессия не указана, используем последнюю или создаем новую
    if session_id is None:
        sessions = database.get_all_sessions()
        if sessions:
            session_id = sessions[0]['session_id']
            print(f"Используем существующую сессию: {sessions[0]['session_name']} (ID: {session_id})")
        else:
            # Создаем новую сессию
            session_name = f"Тестовая сессия 100 заказов {datetime.now().strftime('%Y%m%d%H%M%S')}"
            session_id = database.add_session(session_name, ADMIN_ID)
            if not session_id:
                print("Ошибка при создании сессии!")
                return
            print(f"Создана новая сессия: {session_name} (ID: {session_id})")
    
    session = database.get_session(session_id)
    if not session:
        print(f"Сессия {session_id} не найдена!")
        return
    
    # Получаем товары сессии
    products = database.get_products_by_session(session_id)
    
    if not products:
        # Добавляем товары если их нет
        print("Добавляем товары в сессию...")
        products_data = [
            {"name": "Яблоки", "price": 500.0, "boxes": 500},
            {"name": "Груши", "price": 600.0, "boxes": 400},
            {"name": "Виноград", "price": 800.0, "boxes": 300},
            {"name": "Персики", "price": 700.0, "boxes": 350},
            {"name": "Сливы", "price": 550.0, "boxes": 450},
        ]
        
        for product_data in products_data:
            product_id = database.add_product(
                session_id=session_id,
                product_name=product_data["name"],
                price=product_data["price"],
                boxes_count=product_data["boxes"],
                created_by=ADMIN_ID
            )
            if product_id:
                print(f"Добавлен товар: {product_data['name']}")
        
        products = database.get_products_by_session(session_id)
    
    if not products:
        print("Нет товаров для создания заказов!")
        return
    
    # Создаем или получаем тестовых пользователей
    conn = sqlite3.connect(database.DB_NAME)
    cursor = conn.cursor()
    
    # Проверяем существующих пользователей
    cursor.execute("SELECT user_id FROM users LIMIT 20")
    existing_users = cursor.fetchall()
    test_users = [user[0] for user in existing_users] if existing_users else []
    
    # Если пользователей мало, создаем больше
    if len(test_users) < 20:
        for i in range(len(test_users), 20):
            user_id = 2000 + i
            try:
                cursor.execute("""
                    INSERT INTO users (user_id, first_name, username, chat_id, is_bot)
                    VALUES (?, ?, ?, ?, 0)
                """, (user_id, f"Пользователь{i+1}", f"user{i+1}", user_id))
                test_users.append(user_id)
            except sqlite3.IntegrityError:
                test_users.append(user_id)
    
    conn.commit()
    conn.close()
    
    # Генерируем тестовые данные для заказов
    first_names = ["Иван", "Мария", "Петр", "Анна", "Сергей", "Елена", "Дмитрий", "Ольга", 
                   "Александр", "Наталья", "Андрей", "Татьяна", "Михаил", "Екатерина", "Владимир"]
    last_names = ["Иванов", "Петров", "Сидоров", "Козлов", "Смирнов", "Попов", "Лебедев", 
                  "Новиков", "Морозов", "Волков", "Соколов", "Лебедев", "Кузнецов", "Попов", "Соколов"]
    
    statuses = ["pending", "processing", "completed", "pending", "pending"]  # Больше pending для теста
    
    print(f"\nСоздание 100 заказов...")
    created_orders = []
    
    # Генерируем заказы с разными датами (за последние 7 дней)
    base_date = datetime.now()
    
    for i in range(100):
        # Случайный пользователь
        user_id = random.choice(test_users) if test_users else 2000
        
        # Случайное имя
        first_name = random.choice(first_names)
        last_name = random.choice(last_names)
        full_name = f"{first_name} {last_name}"
        
        # Случайный телефон
        phone = f"+7900{random.randint(1000000, 9999999)}"
        
        # Случайные товары (1-3 товара в заказе)
        num_items = random.randint(1, 3)
        selected_products = random.sample(products, min(num_items, len(products)))
        
        items = []
        for product in selected_products:
            quantity = random.randint(1, 5)  # 1-5 ящиков каждого товара
            items.append({
                "product_id": product['product_id'],
                "quantity": quantity,
                "price": product['price']
            })
        
        # Создаем заказ
        order_id = database.create_order(
            user_id=user_id,
            session_id=session_id,
            phone_number=phone,
            full_name=full_name,
            items=items
        )
        
        if order_id:
            # Устанавливаем случайный статус
            status = random.choice(statuses)
            database.update_order_status(order_id, status)
            
            # Устанавливаем случайную дату (за последние 7 дней)
            days_ago = random.randint(0, 7)
            hours_ago = random.randint(0, 23)
            order_date = (base_date - timedelta(days=days_ago, hours=hours_ago)).strftime('%Y-%m-%d %H:%M:%S')
            
            # Обновляем дату заказа в БД
            conn = sqlite3.connect(database.DB_NAME)
            cursor = conn.cursor()
            cursor.execute("UPDATE orders SET created_at = ? WHERE order_id = ?", (order_date, order_id))
            conn.commit()
            conn.close()
            
            created_orders.append(order_id)
            
            if (i + 1) % 10 == 0:
                print(f"Создано заказов: {i + 1}/100")
    
    # Активируем торговлю для сессии
    database.set_session_trading_status(session_id, True)
    
    print(f"\n✅ Успешно создано {len(created_orders)} заказов!")
    print(f"📊 Статистика сессии '{session['session_name']}':")
    
    # Подсчитываем статистику
    orders = database.get_session_orders(session_id)
    completed = sum(1 for o in orders if o['status'] == 'completed')
    pending = sum(1 for o in orders if o['status'] == 'pending')
    processing = sum(1 for o in orders if o['status'] == 'processing')
    
    print(f"   - Всего заказов: {len(orders)}")
    print(f"   - Выдано: {completed}")
    print(f"   - Ожидает обработки: {pending}")
    print(f"   - В обработке: {processing}")
    print(f"   - Торговля: Активна")
    print(f"\n💡 Session ID: {session_id}")


if __name__ == "__main__":
    import sys
    
    # Инициализируем БД
    database.init_database()
    
    # Можно указать ID сессии как аргумент
    session_id = None
    if len(sys.argv) > 1:
        try:
            session_id = int(sys.argv[1])
        except ValueError:
            print("Неверный формат ID сессии. Используется автоматический выбор.")
    
    # Создаем 100 заказов
    create_100_orders(session_id)
