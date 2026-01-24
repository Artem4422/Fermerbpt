import sqlite3
import logging
from datetime import datetime
from typing import Optional

logger = logging.getLogger(__name__)

DB_NAME = "bot_database.db"


def init_database():
    """Инициализация базы данных и создание таблиц"""
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
            user_id INTEGER PRIMARY KEY,
            username TEXT,
            first_name TEXT NOT NULL,
            last_name TEXT,
            language_code TEXT,
            is_bot INTEGER DEFAULT 0,
            is_premium INTEGER DEFAULT 0,
            added_to_attachment_menu INTEGER DEFAULT 0,
            can_join_groups INTEGER DEFAULT 1,
            can_read_all_group_messages INTEGER DEFAULT 0,
            supports_inline_queries INTEGER DEFAULT 0,
            chat_id INTEGER,
            first_seen TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            last_seen TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            total_messages INTEGER DEFAULT 0
        )
    """)
    
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS admins (
            user_id INTEGER PRIMARY KEY,
            added_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users(user_id)
        )
    """)
    
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS managers (
            user_id INTEGER PRIMARY KEY,
            added_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users(user_id)
        )
    """)
    
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS sessions (
            session_id INTEGER PRIMARY KEY AUTOINCREMENT,
            session_name TEXT NOT NULL UNIQUE,
            is_active INTEGER DEFAULT 0,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            created_by INTEGER,
            FOREIGN KEY (created_by) REFERENCES users(user_id)
        )
    """)
    
    # Добавляем поле is_active, если таблица уже существует
    try:
        cursor.execute("ALTER TABLE sessions ADD COLUMN is_active INTEGER DEFAULT 0")
    except sqlite3.OperationalError:
        pass  # Поле уже существует
    
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS products (
            product_id INTEGER PRIMARY KEY AUTOINCREMENT,
            session_id INTEGER NOT NULL,
            product_name TEXT NOT NULL,
            price REAL NOT NULL,
            boxes_count INTEGER NOT NULL DEFAULT 0,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            created_by INTEGER,
            FOREIGN KEY (session_id) REFERENCES sessions(session_id),
            FOREIGN KEY (created_by) REFERENCES users(user_id)
        )
    """)
    
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS settings (
            setting_key TEXT PRIMARY KEY,
            setting_value TEXT NOT NULL,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS orders (
            order_id INTEGER PRIMARY KEY AUTOINCREMENT,
            order_number TEXT NOT NULL UNIQUE,
            user_id INTEGER NOT NULL,
            session_id INTEGER NOT NULL,
            phone_number TEXT,
            full_name TEXT,
            total_amount REAL NOT NULL DEFAULT 0,
            status TEXT DEFAULT 'pending',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users(user_id),
            FOREIGN KEY (session_id) REFERENCES sessions(session_id)
        )
    """)
    
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS order_items (
            item_id INTEGER PRIMARY KEY AUTOINCREMENT,
            order_id INTEGER NOT NULL,
            product_id INTEGER NOT NULL,
            quantity INTEGER NOT NULL,
            price REAL NOT NULL,
            FOREIGN KEY (order_id) REFERENCES orders(order_id),
            FOREIGN KEY (product_id) REFERENCES products(product_id)
        )
    """)
    
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS user_session_limits (
            user_id INTEGER NOT NULL,
            session_id INTEGER NOT NULL,
            boxes_purchased INTEGER DEFAULT 0,
            PRIMARY KEY (user_id, session_id),
            FOREIGN KEY (user_id) REFERENCES users(user_id),
            FOREIGN KEY (session_id) REFERENCES sessions(session_id)
        )
    """)
    
    # Инициализируем лимит на человека значением по умолчанию, если его нет
    cursor.execute("SELECT setting_key FROM settings WHERE setting_key = 'limit_per_person'")
    if not cursor.fetchone():
        cursor.execute("""
            INSERT INTO settings (setting_key, setting_value)
            VALUES ('limit_per_person', '0')
        """)
    
    conn.commit()
    conn.close()
    logger.info("База данных инициализирована")


def save_or_update_user(user, chat_id: int):
    """Сохраняет или обновляет информацию о пользователе"""
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    
    # Проверяем, существует ли пользователь
    cursor.execute("SELECT user_id FROM users WHERE user_id = ?", (user.id,))
    exists = cursor.fetchone()
    
    if exists:
        # Обновляем информацию
        cursor.execute("""
            UPDATE users SET
                username = ?,
                first_name = ?,
                last_name = ?,
                language_code = ?,
                is_bot = ?,
                is_premium = ?,
                added_to_attachment_menu = ?,
                can_join_groups = ?,
                can_read_all_group_messages = ?,
                supports_inline_queries = ?,
                chat_id = ?,
                last_seen = CURRENT_TIMESTAMP,
                total_messages = total_messages + 1
            WHERE user_id = ?
        """, (
            user.username,
            user.first_name,
            user.last_name,
            user.language_code,
            1 if user.is_bot else 0,
            1 if getattr(user, 'is_premium', False) else 0,
            1 if getattr(user, 'added_to_attachment_menu', False) else 0,
            1 if getattr(user, 'can_join_groups', True) else 0,
            1 if getattr(user, 'can_read_all_group_messages', False) else 0,
            1 if getattr(user, 'supports_inline_queries', False) else 0,
            chat_id,
            user.id
        ))
        logger.info(f"Обновлена информация о пользователе {user.id}")
    else:
        # Создаем новую запись
        cursor.execute("""
            INSERT INTO users (
                user_id, username, first_name, last_name, language_code,
                is_bot, is_premium, added_to_attachment_menu,
                can_join_groups, can_read_all_group_messages,
                supports_inline_queries, chat_id, first_seen, last_seen, total_messages
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP, 1)
        """, (
            user.id,
            user.username,
            user.first_name,
            user.last_name,
            user.language_code,
            1 if user.is_bot else 0,
            1 if getattr(user, 'is_premium', False) else 0,
            1 if getattr(user, 'added_to_attachment_menu', False) else 0,
            1 if getattr(user, 'can_join_groups', True) else 0,
            1 if getattr(user, 'can_read_all_group_messages', False) else 0,
            1 if getattr(user, 'supports_inline_queries', False) else 0,
            chat_id
        ))
        logger.info(f"Сохранен новый пользователь {user.id} ({user.first_name})")
    
    conn.commit()
    conn.close()


def get_user_info(user_id: int) -> Optional[dict]:
    """Получает информацию о пользователе из базы данных"""
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    
    cursor.execute("SELECT * FROM users WHERE user_id = ?", (user_id,))
    row = cursor.fetchone()
    conn.close()
    
    if row:
        columns = [
            'user_id', 'username', 'first_name', 'last_name', 'language_code',
            'is_bot', 'is_premium', 'added_to_attachment_menu',
            'can_join_groups', 'can_read_all_group_messages',
            'supports_inline_queries', 'chat_id', 'first_seen', 'last_seen', 'total_messages'
        ]
        return dict(zip(columns, row))
    return None


def is_admin(user_id: int) -> bool:
    """Проверяет, является ли пользователь администратором"""
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("SELECT user_id FROM admins WHERE user_id = ?", (user_id,))
    result = cursor.fetchone() is not None
    conn.close()
    return result


def is_manager(user_id: int) -> bool:
    """Проверяет, является ли пользователь менеджером"""
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("SELECT user_id FROM managers WHERE user_id = ?", (user_id,))
    result = cursor.fetchone() is not None
    conn.close()
    return result


def add_admin(user_id: int) -> bool:
    """Добавляет администратора"""
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    try:
        cursor.execute("INSERT OR IGNORE INTO admins (user_id) VALUES (?)", (user_id,))
        conn.commit()
        success = cursor.rowcount > 0
        conn.close()
        return success
    except:
        conn.close()
        return False


def remove_admin(user_id: int) -> bool:
    """Удаляет администратора"""
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("DELETE FROM admins WHERE user_id = ?", (user_id,))
    conn.commit()
    success = cursor.rowcount > 0
    conn.close()
    return success


def add_manager(user_id: int) -> bool:
    """Добавляет менеджера"""
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    try:
        cursor.execute("INSERT OR IGNORE INTO managers (user_id) VALUES (?)", (user_id,))
        conn.commit()
        success = cursor.rowcount > 0
        conn.close()
        return success
    except:
        conn.close()
        return False


def remove_manager(user_id: int) -> bool:
    """Удаляет менеджера"""
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("DELETE FROM managers WHERE user_id = ?", (user_id,))
    conn.commit()
    success = cursor.rowcount > 0
    conn.close()
    return success


def add_session(session_name: str, created_by: int) -> Optional[int]:
    """Добавляет новую сессию"""
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    try:
        cursor.execute("""
            INSERT INTO sessions (session_name, created_by)
            VALUES (?, ?)
        """, (session_name, created_by))
        conn.commit()
        session_id = cursor.lastrowid
        conn.close()
        logger.info(f"Создана сессия '{session_name}' пользователем {created_by}")
        return session_id
    except sqlite3.IntegrityError:
        conn.close()
        return None
    except Exception as e:
        logger.error(f"Ошибка при создании сессии: {e}")
        conn.close()
        return None


def get_all_sessions() -> list:
    """Получает список всех сессий"""
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("SELECT session_id, session_name FROM sessions ORDER BY created_at DESC")
    sessions = cursor.fetchall()
    conn.close()
    return [{"session_id": s[0], "session_name": s[1]} for s in sessions]


def get_active_sessions() -> list:
    """Получает список активных сессий"""
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("SELECT session_id, session_name FROM sessions WHERE is_active = 1 ORDER BY created_at DESC")
    sessions = cursor.fetchall()
    conn.close()
    return [{"session_id": s[0], "session_name": s[1]} for s in sessions]


def delete_session(session_id: int) -> bool:
    """Удаляет сессию и связанные данные"""
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    try:
        # Проверяем, существует ли сессия
        cursor.execute("SELECT session_id FROM sessions WHERE session_id = ?", (session_id,))
        if not cursor.fetchone():
            conn.close()
            return False
        
        # Отключаем проверку foreign key для этой операции
        cursor.execute("PRAGMA foreign_keys = OFF")
        
        # Удаляем связанные записи из user_session_limits
        cursor.execute("DELETE FROM user_session_limits WHERE session_id = ?", (session_id,))
        
        # Удаляем товары сессии
        cursor.execute("DELETE FROM products WHERE session_id = ?", (session_id,))
        
        # Удаляем саму сессию
        cursor.execute("DELETE FROM sessions WHERE session_id = ?", (session_id,))
        
        # Включаем обратно проверку foreign key
        cursor.execute("PRAGMA foreign_keys = ON")
        
        conn.commit()
        conn.close()
        logger.info(f"Сессия {session_id} и связанные данные удалены")
        return True
    except Exception as e:
        logger.error(f"Ошибка при удалении сессии: {e}")
        conn.rollback()
        conn.close()
        return False


def get_session(session_id: int) -> Optional[dict]:
    """Получает информацию о сессии"""
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("SELECT session_id, session_name, is_active, created_at FROM sessions WHERE session_id = ?", (session_id,))
    row = cursor.fetchone()
    conn.close()
    if row:
        return {
            "session_id": row[0],
            "session_name": row[1],
            "is_active": bool(row[2]),
            "created_at": row[3]
        }
    return None


def add_product(session_id: int, product_name: str, price: float, boxes_count: int, created_by: int) -> Optional[int]:
    """Добавляет новый товар"""
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    try:
        cursor.execute("""
            INSERT INTO products (session_id, product_name, price, boxes_count, created_by)
            VALUES (?, ?, ?, ?, ?)
        """, (session_id, product_name, price, boxes_count, created_by))
        conn.commit()
        product_id = cursor.lastrowid
        conn.close()
        logger.info(f"Создан товар '{product_name}' для сессии {session_id} пользователем {created_by}")
        return product_id
    except Exception as e:
        logger.error(f"Ошибка при создании товара: {e}")
        conn.close()
        return None


def get_products_by_session(session_id: int) -> list:
    """Получает список товаров для сессии"""
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("""
        SELECT product_id, product_name, price, boxes_count 
        FROM products 
        WHERE session_id = ? 
        ORDER BY created_at DESC
    """, (session_id,))
    products = cursor.fetchall()
    conn.close()
    return [{"product_id": p[0], "product_name": p[1], "price": p[2], "boxes_count": p[3]} for p in products]


def get_product(product_id: int) -> Optional[dict]:
    """Получает информацию о товаре"""
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("""
        SELECT product_id, session_id, product_name, price, boxes_count 
        FROM products 
        WHERE product_id = ?
    """, (product_id,))
    row = cursor.fetchone()
    conn.close()
    if row:
        return {
            "product_id": row[0],
            "session_id": row[1],
            "product_name": row[2],
            "price": row[3],
            "boxes_count": row[4]
        }
    return None


def delete_product(product_id: int) -> bool:
    """Удаляет товар"""
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("DELETE FROM products WHERE product_id = ?", (product_id,))
    conn.commit()
    success = cursor.rowcount > 0
    conn.close()
    if success:
        logger.info(f"Товар {product_id} удален")
    return success


def update_product_boxes_count(product_id: int, boxes_count: int) -> bool:
    """Обновляет количество ящиков товара"""
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    try:
        cursor.execute("UPDATE products SET boxes_count = ? WHERE product_id = ?", (boxes_count, product_id))
        conn.commit()
        conn.close()
        logger.info(f"Количество ящиков товара {product_id} обновлено на {boxes_count}")
        return True
    except Exception as e:
        logger.error(f"Ошибка при обновлении количества ящиков: {e}")
        conn.close()
        return False


def set_limit_per_person(limit: int) -> bool:
    """Устанавливает лимит ящиков на одного человека"""
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    try:
        cursor.execute("""
            INSERT OR REPLACE INTO settings (setting_key, setting_value, updated_at)
            VALUES ('limit_per_person', ?, CURRENT_TIMESTAMP)
        """, (str(limit),))
        conn.commit()
        conn.close()
        logger.info(f"Установлен лимит на человека: {limit} ящиков")
        return True
    except Exception as e:
        logger.error(f"Ошибка при установке лимита: {e}")
        conn.close()
        return False


def get_limit_per_person() -> int:
    """Получает лимит ящиков на одного человека"""
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("SELECT setting_value FROM settings WHERE setting_key = 'limit_per_person'")
    row = cursor.fetchone()
    conn.close()
    if row:
        try:
            return int(row[0])
        except (ValueError, TypeError):
            return 0
    return 0


def set_session_trading_status(session_id: int, is_active: bool) -> bool:
    """Устанавливает статус торговли для конкретной сессии"""
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    try:
        cursor.execute("""
            UPDATE sessions SET is_active = ? WHERE session_id = ?
        """, (1 if is_active else 0, session_id))
        conn.commit()
        success = cursor.rowcount > 0
        conn.close()
        if success:
            status_text = "открыта" if is_active else "закрыта"
            logger.info(f"Торговля для сессии {session_id} {status_text}")
        return success
    except Exception as e:
        logger.error(f"Ошибка при установке статуса торговли для сессии: {e}")
        conn.close()
        return False


def is_session_trading_active(session_id: int) -> bool:
    """Проверяет, активна ли торговля для конкретной сессии"""
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("SELECT is_active FROM sessions WHERE session_id = ?", (session_id,))
    row = cursor.fetchone()
    conn.close()
    if row:
        return bool(row[0])
    return False


def get_user_session_boxes_purchased(user_id: int, session_id: int) -> int:
    """Получает количество купленных ящиков пользователем в сессии"""
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("""
        SELECT boxes_purchased FROM user_session_limits 
        WHERE user_id = ? AND session_id = ?
    """, (user_id, session_id))
    row = cursor.fetchone()
    conn.close()
    return row[0] if row else 0


def get_user_available_boxes(user_id: int, session_id: int, product_id: int = None) -> int:
    """Получает доступное количество ящиков для покупки пользователем в сессии"""
    limit = get_limit_per_person()
    purchased = get_user_session_boxes_purchased(user_id, session_id)
    
    if limit == 0:
        # Без ограничений по лимиту, но проверяем доступность товара
        if product_id:
            product = get_product(product_id)
            if product:
                return product['boxes_count']
        return 999999  # Без ограничений
    
    available_by_limit = limit - purchased
    
    # Если указан товар, учитываем его доступность
    if product_id:
        product = get_product(product_id)
        if product:
            available_by_product = product['boxes_count']
            return min(available_by_limit, available_by_product)
    
    return max(0, available_by_limit)


def generate_order_number() -> str:
    """Генерирует уникальный номер заказа"""
    import random
    import string
    while True:
        # Генерируем 6-значный номер заказа
        order_num = ''.join(random.choices(string.digits, k=6))
        conn = sqlite3.connect(DB_NAME)
        cursor = conn.cursor()
        cursor.execute("SELECT order_id FROM orders WHERE order_number = ?", (order_num,))
        if not cursor.fetchone():
            conn.close()
            return order_num
        conn.close()


def create_order(user_id: int, session_id: int, phone_number: str, full_name: str, items: list) -> Optional[int]:
    """Создает заказ"""
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    try:
        order_number = generate_order_number()
        total_amount = sum(item['quantity'] * item['price'] for item in items)
        
        cursor.execute("""
            INSERT INTO orders (order_number, user_id, session_id, phone_number, full_name, total_amount)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (order_number, user_id, session_id, phone_number, full_name, total_amount))
        
        order_id = cursor.lastrowid
        
        # Добавляем товары в заказ и уменьшаем количество доступных ящиков
        for item in items:
            cursor.execute("""
                INSERT INTO order_items (order_id, product_id, quantity, price)
                VALUES (?, ?, ?, ?)
            """, (order_id, item['product_id'], item['quantity'], item['price']))
            
            # Уменьшаем количество доступных ящиков товара
            cursor.execute("""
                UPDATE products 
                SET boxes_count = boxes_count - ? 
                WHERE product_id = ?
            """, (item['quantity'], item['product_id']))
        
        # Обновляем количество купленных ящиков пользователем в сессии
        total_boxes = sum(item['quantity'] for item in items)
        cursor.execute("""
            INSERT INTO user_session_limits (user_id, session_id, boxes_purchased)
            VALUES (?, ?, ?)
            ON CONFLICT(user_id, session_id) 
            DO UPDATE SET boxes_purchased = boxes_purchased + ?
        """, (user_id, session_id, total_boxes, total_boxes))
        
        conn.commit()
        conn.close()
        logger.info(f"Создан заказ {order_number} пользователем {user_id}")
        return order_id
    except Exception as e:
        logger.error(f"Ошибка при создании заказа: {e}")
        conn.close()
        return None


def get_order(order_id: int) -> Optional[dict]:
    """Получает информацию о заказе"""
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("""
        SELECT order_id, order_number, user_id, session_id, phone_number, full_name, 
               total_amount, status, created_at
        FROM orders WHERE order_id = ?
    """, (order_id,))
    row = cursor.fetchone()
    conn.close()
    if row:
        return {
            "order_id": row[0],
            "order_number": row[1],
            "user_id": row[2],
            "session_id": row[3],
            "phone_number": row[4],
            "full_name": row[5],
            "total_amount": row[6],
            "status": row[7],
            "created_at": row[8]
        }
    return None


def get_order_items(order_id: int) -> list:
    """Получает товары заказа"""
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("""
        SELECT oi.item_id, oi.product_id, oi.quantity, oi.price, p.product_name
        FROM order_items oi
        JOIN products p ON oi.product_id = p.product_id
        WHERE oi.order_id = ?
    """, (order_id,))
    items = cursor.fetchall()
    conn.close()
    return [
        {
            "item_id": item[0],
            "product_id": item[1],
            "quantity": item[2],
            "price": item[3],
            "product_name": item[4]
        }
        for item in items
    ]


def get_order_status_ru(status: str) -> str:
    """Переводит статус заказа на русский язык"""
    status_map = {
        'pending': 'Ожидает обработки',
        'processing': 'В обработке',
        'completed': 'Завершен',
        'cancelled': 'Отменен'
    }
    return status_map.get(status, status)


def find_order_by_number(order_number: str) -> Optional[dict]:
    """Находит заказ по номеру"""
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("""
        SELECT order_id, order_number, user_id, session_id, phone_number, full_name, 
               total_amount, status, created_at
        FROM orders WHERE order_number = ?
    """, (order_number,))
    row = cursor.fetchone()
    conn.close()
    if row:
        return {
            "order_id": row[0],
            "order_number": row[1],
            "user_id": row[2],
            "session_id": row[3],
            "phone_number": row[4],
            "full_name": row[5],
            "total_amount": row[6],
            "status": row[7],
            "created_at": row[8]
        }
    return None


def update_order_status(order_id: int, status: str) -> bool:
    """Обновляет статус заказа"""
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    try:
        cursor.execute("UPDATE orders SET status = ? WHERE order_id = ?", (status, order_id))
        conn.commit()
        conn.close()
        return True
    except Exception as e:
        logger.error(f"Ошибка при обновлении статуса заказа: {e}")
        conn.close()
        return False


def get_session_orders(session_id: int) -> list:
    """Получает все заказы для сессии"""
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("""
        SELECT o.order_id, o.order_number, o.user_id, o.phone_number, o.full_name, 
               o.total_amount, o.status, o.created_at,
               GROUP_CONCAT(p.product_name || ' x' || oi.quantity || ' (' || oi.price || '₽)') as items
        FROM orders o
        LEFT JOIN order_items oi ON o.order_id = oi.order_id
        LEFT JOIN products p ON oi.product_id = p.product_id
        WHERE o.session_id = ?
        GROUP BY o.order_id
        ORDER BY o.created_at DESC
    """, (session_id,))
    orders = cursor.fetchall()
    conn.close()
    return [
        {
            "order_id": order[0],
            "order_number": order[1],
            "user_id": order[2],
            "phone_number": order[3],
            "full_name": order[4],
            "total_amount": order[5],
            "status": order[6],
            "created_at": order[7],
            "items": order[8] or "Нет товаров"
        }
        for order in orders
    ]


def get_orders_by_period(period: str) -> list:
    """Получает все заказы за указанный период"""
    from datetime import datetime, timedelta
    
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    
    now = datetime.now()
    
    if period == "week":
        start_date = (now - timedelta(days=7)).strftime('%Y-%m-%d %H:%M:%S')
    elif period == "month":
        start_date = (now - timedelta(days=30)).strftime('%Y-%m-%d %H:%M:%S')
    elif period == "year":
        start_date = (now - timedelta(days=365)).strftime('%Y-%m-%d %H:%M:%S')
    else:  # all_time
        start_date = None
    
    if start_date:
        cursor.execute("""
            SELECT o.order_id, o.order_number, o.user_id, o.session_id, o.phone_number, o.full_name, 
                   o.total_amount, o.status, o.created_at,
                   GROUP_CONCAT(p.product_name || ' x' || oi.quantity || ' (' || oi.price || '₽)') as items
            FROM orders o
            LEFT JOIN order_items oi ON o.order_id = oi.order_id
            LEFT JOIN products p ON oi.product_id = p.product_id
            WHERE o.created_at >= ?
            GROUP BY o.order_id
            ORDER BY o.created_at DESC
        """, (start_date,))
    else:
        cursor.execute("""
            SELECT o.order_id, o.order_number, o.user_id, o.session_id, o.phone_number, o.full_name, 
                   o.total_amount, o.status, o.created_at,
                   GROUP_CONCAT(p.product_name || ' x' || oi.quantity || ' (' || oi.price || '₽)') as items
            FROM orders o
            LEFT JOIN order_items oi ON o.order_id = oi.order_id
            LEFT JOIN products p ON oi.product_id = p.product_id
            GROUP BY o.order_id
            ORDER BY o.created_at DESC
        """)
    
    orders = cursor.fetchall()
    conn.close()
    return [
        {
            "order_id": order[0],
            "order_number": order[1],
            "user_id": order[2],
            "session_id": order[3],
            "phone_number": order[4],
            "full_name": order[5],
            "total_amount": order[6],
            "status": order[7],
            "created_at": order[8],
            "items": order[9] or "Нет товаров"
        }
        for order in orders
    ]


def get_user_cart(user_id: int, session_id: int) -> list:
    """Получает корзину пользователя для сессии"""
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("""
        SELECT o.order_id, o.order_number, o.total_amount, o.status, o.created_at,
               GROUP_CONCAT(p.product_name || ' x' || oi.quantity) as items
        FROM orders o
        JOIN order_items oi ON o.order_id = oi.order_id
        JOIN products p ON oi.product_id = p.product_id
        WHERE o.user_id = ? AND o.session_id = ?
        GROUP BY o.order_id
        ORDER BY o.created_at DESC
    """, (user_id, session_id))
    orders = cursor.fetchall()
    conn.close()
    return [
        {
            "order_id": order[0],
            "order_number": order[1],
            "total_amount": order[2],
            "status": get_order_status_ru(order[3]),
            "created_at": order[4],
            "items": order[5]
        }
        for order in orders
    ]
