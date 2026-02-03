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
    # Добавляем поле description для сессии (название + описание/ссылка)
    try:
        cursor.execute("ALTER TABLE sessions ADD COLUMN description TEXT DEFAULT ''")
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
            session_order_number INTEGER,
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
    
    # Добавляем поле session_order_number, если таблица уже существует
    try:
        cursor.execute("ALTER TABLE orders ADD COLUMN session_order_number INTEGER")
    except sqlite3.OperationalError:
        pass  # Поле уже существует
    
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
    
    # Добавляем phone_number и full_name в users, если их ещё нет
    for col in ('phone_number', 'full_name'):
        try:
            cursor.execute(f"ALTER TABLE users ADD COLUMN {col} TEXT")
        except sqlite3.OperationalError:
            pass
    
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
            'supports_inline_queries', 'chat_id', 'first_seen', 'last_seen', 'total_messages',
            'phone_number', 'full_name'
        ]
        # Учитываем случай, когда в БД ещё нет колонок phone_number, full_name
        result = dict(zip(columns[:len(row)], row))
        if 'phone_number' not in result:
            result['phone_number'] = None
        if 'full_name' not in result:
            result['full_name'] = None
        return result
    return None


def update_user_profile(user_id: int, phone_number: Optional[str] = None, full_name: Optional[str] = None) -> bool:
    """Обновляет телефон и/или ФИО пользователя в профиле"""
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    try:
        if phone_number is not None and full_name is not None:
            cursor.execute(
                "UPDATE users SET phone_number = ?, full_name = ? WHERE user_id = ?",
                (phone_number, full_name, user_id)
            )
        elif phone_number is not None:
            cursor.execute(
                "UPDATE users SET phone_number = ? WHERE user_id = ?",
                (phone_number, user_id)
            )
        elif full_name is not None:
            cursor.execute(
                "UPDATE users SET full_name = ? WHERE user_id = ?",
                (full_name, user_id)
            )
        else:
            conn.close()
            return False
        conn.commit()
        conn.close()
        return True
    except Exception:
        conn.close()
        return False


def is_registered(user_id: int) -> bool:
    """Проверяет, зарегистрирован ли пользователь (указан ли телефон)"""
    info = get_user_info(user_id)
    return bool(info and info.get('phone_number'))


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


def add_session(session_name: str, created_by: int, description: str = "") -> Optional[int]:
    """Добавляет новую сессию (имя и описание; описание может быть ссылкой)."""
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    try:
        cursor.execute("""
            INSERT INTO sessions (session_name, description, created_by)
            VALUES (?, ?, ?)
        """, (session_name, description or "", created_by))
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
    """Получает список всех сессий (с полем description)."""
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("SELECT session_id, session_name, COALESCE(description, '') FROM sessions ORDER BY created_at DESC")
    sessions = cursor.fetchall()
    conn.close()
    return [{"session_id": s[0], "session_name": s[1], "description": s[2] or ""} for s in sessions]


def get_active_sessions() -> list:
    """Получает список активных сессий (с полем description)."""
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("SELECT session_id, session_name, COALESCE(description, '') FROM sessions WHERE is_active = 1 ORDER BY created_at DESC")
    sessions = cursor.fetchall()
    conn.close()
    return [{"session_id": s[0], "session_name": s[1], "description": s[2] or ""} for s in sessions]


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
    """Получает информацию о сессии (включая description)."""
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("SELECT session_id, session_name, is_active, created_at, COALESCE(description, '') FROM sessions WHERE session_id = ?", (session_id,))
    row = cursor.fetchone()
    conn.close()
    if row:
        return {
            "session_id": row[0],
            "session_name": row[1],
            "is_active": bool(row[2]),
            "created_at": row[3],
            "description": row[4] or ""
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
    """Получает количество купленных ящиков пользователем в сессии (только выданные заказы)"""
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    # Считаем только заказы со статусом 'completed'
    cursor.execute("""
        SELECT COALESCE(SUM(oi.quantity), 0)
        FROM orders o
        JOIN order_items oi ON o.order_id = oi.order_id
        WHERE o.user_id = ? AND o.session_id = ? AND o.status = 'completed'
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


def generate_session_order_number(session_id: int) -> int:
    """Генерирует номер заказа по сессии (следующий по порядку)"""
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    # Находим максимальный номер заказа в этой сессии
    cursor.execute("""
        SELECT MAX(session_order_number) 
        FROM orders 
        WHERE session_id = ? AND session_order_number IS NOT NULL
    """, (session_id,))
    result = cursor.fetchone()
    max_number = result[0] if result[0] else 0
    conn.close()
    return max_number + 1


def create_order(user_id: int, session_id: int, phone_number: str, full_name: str, items: list) -> Optional[int]:
    """Создает заказ"""
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    try:
        order_number = generate_order_number()
        session_order_number = generate_session_order_number(session_id)
        total_amount = sum(item['quantity'] * item['price'] for item in items)
        
        cursor.execute("""
            INSERT INTO orders (order_number, session_order_number, user_id, session_id, phone_number, full_name, total_amount)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (order_number, session_order_number, user_id, session_id, phone_number, full_name, total_amount))
        
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
        
        # НЕ обновляем лимит при создании заказа - лимит будет обновлен только при выдаче заказа (статус completed)
        
        conn.commit()
        conn.close()
        logger.info(f"Создан заказ {order_number} (№{session_order_number} по сессии) пользователем {user_id}")
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
        SELECT order_id, order_number, session_order_number, user_id, session_id, phone_number, full_name, 
               total_amount, status, created_at
        FROM orders WHERE order_id = ?
    """, (order_id,))
    row = cursor.fetchone()
    conn.close()
    if row:
        return {
            "order_id": row[0],
            "order_number": row[1],
            "session_order_number": row[2],
            "user_id": row[3],
            "session_id": row[4],
            "phone_number": row[5],
            "full_name": row[6],
            "total_amount": row[7],
            "status": row[8],
            "created_at": row[9]
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


def get_order_item(item_id: int) -> Optional[dict]:
    """Получает информацию о товаре в заказе"""
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("""
        SELECT oi.item_id, oi.order_id, oi.product_id, oi.quantity, oi.price, p.product_name
        FROM order_items oi
        JOIN products p ON oi.product_id = p.product_id
        WHERE oi.item_id = ?
    """, (item_id,))
    row = cursor.fetchone()
    conn.close()
    if row:
        return {
            "item_id": row[0],
            "order_id": row[1],
            "product_id": row[2],
            "quantity": row[3],
            "price": row[4],
            "product_name": row[5]
        }
    return None


def delete_order_item(item_id: int, order_id: int) -> bool:
    """Удаляет товар из заказа"""
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    try:
        # Получаем информацию о товаре перед удалением
        cursor.execute("SELECT product_id, quantity FROM order_items WHERE item_id = ?", (item_id,))
        item_data = cursor.fetchone()
        
        if not item_data:
            conn.close()
            return False
        
        product_id, quantity = item_data
        
        # Получаем статус заказа
        cursor.execute("SELECT status FROM orders WHERE order_id = ?", (order_id,))
        order_status = cursor.fetchone()
        
        if order_status and order_status[0] == 'completed':
            # Если заказ выдан, возвращаем лимит
            cursor.execute("SELECT user_id, session_id FROM orders WHERE order_id = ?", (order_id,))
            order_info = cursor.fetchone()
            if order_info:
                user_id, session_id = order_info
                cursor.execute("""
                    UPDATE user_session_limits 
                    SET boxes_purchased = boxes_purchased - ?
                    WHERE user_id = ? AND session_id = ?
                """, (quantity, user_id, session_id))
        
        # Возвращаем количество ящиков товара
        cursor.execute("""
            UPDATE products 
            SET boxes_count = boxes_count + ? 
            WHERE product_id = ?
        """, (quantity, product_id))
        
        # Удаляем товар из заказа
        cursor.execute("DELETE FROM order_items WHERE item_id = ?", (item_id,))
        
        # Пересчитываем общую сумму заказа
        cursor.execute("""
            SELECT SUM(oi.quantity * oi.price)
            FROM order_items oi
            WHERE oi.order_id = ?
        """, (order_id,))
        new_total = cursor.fetchone()[0] or 0
        cursor.execute("UPDATE orders SET total_amount = ? WHERE order_id = ?", (new_total, order_id))
        
        conn.commit()
        conn.close()
        logger.info(f"Товар {item_id} удален из заказа {order_id}")
        return True
    except Exception as e:
        logger.error(f"Ошибка при удалении товара из заказа: {e}")
        conn.rollback()
        conn.close()
        return False


def update_order_item_quantity(item_id: int, new_quantity: int) -> bool:
    """Обновляет количество товара в заказе"""
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    try:
        # Получаем текущее количество и информацию о заказе
        cursor.execute("""
            SELECT oi.quantity, oi.product_id, o.order_id, o.status, o.user_id, o.session_id
            FROM order_items oi
            JOIN orders o ON oi.order_id = o.order_id
            WHERE oi.item_id = ?
        """, (item_id,))
        item_data = cursor.fetchone()
        
        if not item_data:
            conn.close()
            return False
        
        old_quantity, product_id, order_id, order_status, user_id, session_id = item_data
        quantity_diff = new_quantity - old_quantity
        
        # Обновляем количество
        cursor.execute("UPDATE order_items SET quantity = ? WHERE item_id = ?", (new_quantity, item_id))
        
        # Обновляем количество ящиков товара
        cursor.execute("""
            UPDATE products 
            SET boxes_count = boxes_count - ? 
            WHERE product_id = ?
        """, (quantity_diff, product_id))
        
        # Если заказ выдан, обновляем лимит
        if order_status == 'completed' and quantity_diff != 0:
            cursor.execute("""
                UPDATE user_session_limits 
                SET boxes_purchased = boxes_purchased + ?
                WHERE user_id = ? AND session_id = ?
            """, (quantity_diff, user_id, session_id))
        
        # Пересчитываем общую сумму заказа
        cursor.execute("""
            SELECT SUM(oi.quantity * oi.price)
            FROM order_items oi
            WHERE oi.order_id = ?
        """, (order_id,))
        new_total = cursor.fetchone()[0] or 0
        cursor.execute("UPDATE orders SET total_amount = ? WHERE order_id = ?", (new_total, order_id))
        
        conn.commit()
        conn.close()
        logger.info(f"Количество товара {item_id} обновлено на {new_quantity}")
        return True
    except Exception as e:
        logger.error(f"Ошибка при обновлении количества товара: {e}")
        conn.rollback()
        conn.close()
        return False


def add_item_to_order(order_id: int, product_id: int, quantity: int) -> bool:
    """Добавляет товар в заказ"""
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    try:
        # Получаем цену товара
        cursor.execute("SELECT price FROM products WHERE product_id = ?", (product_id,))
        product_data = cursor.fetchone()
        
        if not product_data:
            conn.close()
            return False
        
        price = product_data[0]
        
        # Получаем информацию о заказе
        cursor.execute("SELECT status, user_id, session_id FROM orders WHERE order_id = ?", (order_id,))
        order_data = cursor.fetchone()
        
        if not order_data:
            conn.close()
            return False
        
        order_status, user_id, session_id = order_data
        
        # Добавляем товар в заказ
        cursor.execute("""
            INSERT INTO order_items (order_id, product_id, quantity, price)
            VALUES (?, ?, ?, ?)
        """, (order_id, product_id, quantity, price))
        
        # Уменьшаем количество ящиков товара
        cursor.execute("""
            UPDATE products 
            SET boxes_count = boxes_count - ? 
            WHERE product_id = ?
        """, (quantity, product_id))
        
        # Если заказ выдан, обновляем лимит
        if order_status == 'completed':
            cursor.execute("""
                INSERT INTO user_session_limits (user_id, session_id, boxes_purchased)
                VALUES (?, ?, ?)
                ON CONFLICT(user_id, session_id) 
                DO UPDATE SET boxes_purchased = boxes_purchased + ?
            """, (user_id, session_id, quantity, quantity))
        
        # Пересчитываем общую сумму заказа
        cursor.execute("""
            SELECT SUM(oi.quantity * oi.price)
            FROM order_items oi
            WHERE oi.order_id = ?
        """, (order_id,))
        new_total = cursor.fetchone()[0] or 0
        cursor.execute("UPDATE orders SET total_amount = ? WHERE order_id = ?", (new_total, order_id))
        
        conn.commit()
        conn.close()
        logger.info(f"Товар {product_id} добавлен в заказ {order_id}")
        return True
    except Exception as e:
        logger.error(f"Ошибка при добавлении товара в заказ: {e}")
        conn.rollback()
        conn.close()
        return False


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
    """Находит заказ по номеру (общему или по сессии)"""
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    
    # Пытаемся найти по общему номеру
    cursor.execute("""
        SELECT order_id, order_number, session_order_number, user_id, session_id, phone_number, full_name, 
               total_amount, status, created_at
        FROM orders WHERE order_number = ?
    """, (order_number,))
    row = cursor.fetchone()
    
    # Если не найдено и номер - число, ищем по номеру сессии
    if not row and order_number.isdigit():
        cursor.execute("""
            SELECT order_id, order_number, session_order_number, user_id, session_id, phone_number, full_name, 
                   total_amount, status, created_at
            FROM orders WHERE session_order_number = ?
        """, (int(order_number),))
        row = cursor.fetchone()
    
    conn.close()
    if row:
        return {
            "order_id": row[0],
            "order_number": row[1],
            "session_order_number": row[2],
            "user_id": row[3],
            "session_id": row[4],
            "phone_number": row[5],
            "full_name": row[6],
            "total_amount": row[7],
            "status": row[8],
            "created_at": row[9]
        }
    return None


def find_orders_by_session_numbers(session_id: int, session_order_numbers: list) -> list:
    """Находит заказы по номерам заказов в сессии"""
    if not session_order_numbers:
        return []
    
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    placeholders = ','.join(['?'] * len(session_order_numbers))
    cursor.execute(f"""
        SELECT order_id, order_number, session_order_number, user_id, session_id, phone_number, full_name, 
               total_amount, status, created_at
        FROM orders 
        WHERE session_id = ? AND session_order_number IN ({placeholders})
    """, (session_id, *session_order_numbers))
    
    rows = cursor.fetchall()
    conn.close()
    
    return [
        {
            "order_id": row[0],
            "order_number": row[1],
            "session_order_number": row[2],
            "user_id": row[3],
            "session_id": row[4],
            "phone_number": row[5],
            "full_name": row[6],
            "total_amount": row[7],
            "status": row[8],
            "created_at": row[9]
        }
        for row in rows
    ]


def bulk_complete_orders(order_ids: list) -> dict:
    """Массово выдает заказы (меняет статус на completed)"""
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    
    result = {
        'success': [],
        'failed': [],
        'already_completed': []
    }
    
    try:
        for order_id in order_ids:
            # Получаем текущий статус и информацию о заказе
            cursor.execute("SELECT status, user_id, session_id FROM orders WHERE order_id = ?", (order_id,))
            order_data = cursor.fetchone()
            
            if not order_data:
                result['failed'].append(order_id)
                continue
            
            old_status, user_id, session_id = order_data
            
            if old_status == 'completed':
                result['already_completed'].append(order_id)
                continue
            
            # Обновляем статус
            cursor.execute("UPDATE orders SET status = ? WHERE order_id = ?", ('completed', order_id))
            
            # Если статус меняется на 'completed', обновляем лимит пользователя
            if old_status != 'completed':
                # Получаем количество ящиков в заказе
                cursor.execute("""
                    SELECT SUM(quantity) FROM order_items WHERE order_id = ?
                """, (order_id,))
                total_boxes = cursor.fetchone()[0] or 0
                
                if total_boxes > 0:
                    # Увеличиваем количество купленных ящиков
                    cursor.execute("""
                        INSERT INTO user_session_limits (user_id, session_id, boxes_purchased)
                        VALUES (?, ?, ?)
                        ON CONFLICT(user_id, session_id) 
                        DO UPDATE SET boxes_purchased = boxes_purchased + ?
                    """, (user_id, session_id, total_boxes, total_boxes))
            
            result['success'].append(order_id)
        
        conn.commit()
        conn.close()
        return result
    except Exception as e:
        logger.error(f"Ошибка при массовой выдаче заказов: {e}")
        conn.rollback()
        conn.close()
        return result


def update_order_status(order_id: int, status: str) -> bool:
    """Обновляет статус заказа и обновляет лимит пользователя при выдаче заказа"""
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    try:
        # Получаем текущий статус заказа
        cursor.execute("SELECT status, user_id, session_id FROM orders WHERE order_id = ?", (order_id,))
        order_data = cursor.fetchone()
        
        if not order_data:
            conn.close()
            return False
        
        old_status = order_data[0]
        user_id = order_data[1]
        session_id = order_data[2]
        
        # Обновляем статус заказа
        cursor.execute("UPDATE orders SET status = ? WHERE order_id = ?", (status, order_id))
        
        # Если статус меняется на 'completed', уменьшаем лимит пользователя
        if status == 'completed' and old_status != 'completed':
            # Получаем количество ящиков в заказе
            cursor.execute("""
                SELECT SUM(quantity) FROM order_items WHERE order_id = ?
            """, (order_id,))
            total_boxes = cursor.fetchone()[0] or 0
            
            if total_boxes > 0:
                # Увеличиваем количество купленных ящиков
                cursor.execute("""
                    INSERT INTO user_session_limits (user_id, session_id, boxes_purchased)
                    VALUES (?, ?, ?)
                    ON CONFLICT(user_id, session_id) 
                    DO UPDATE SET boxes_purchased = boxes_purchased + ?
                """, (user_id, session_id, total_boxes, total_boxes))
        
        # Если статус меняется с 'completed' на другой, возвращаем лимит обратно
        elif old_status == 'completed' and status != 'completed':
            # Получаем количество ящиков в заказе
            cursor.execute("""
                SELECT SUM(quantity) FROM order_items WHERE order_id = ?
            """, (order_id,))
            total_boxes = cursor.fetchone()[0] or 0
            
            if total_boxes > 0:
                # Уменьшаем количество купленных ящиков
                cursor.execute("""
                    UPDATE user_session_limits 
                    SET boxes_purchased = boxes_purchased - ?
                    WHERE user_id = ? AND session_id = ?
                """, (total_boxes, user_id, session_id))
        
        conn.commit()
        conn.close()
        return True
    except Exception as e:
        logger.error(f"Ошибка при обновлении статуса заказа: {e}")
        conn.rollback()
        conn.close()
        return False


def delete_order(order_id: int) -> bool:
    """Удаляет заказ и все связанные данные"""
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    try:
        # Получаем информацию о заказе перед удалением
        cursor.execute("SELECT status, user_id, session_id FROM orders WHERE order_id = ?", (order_id,))
        order_data = cursor.fetchone()
        
        if not order_data:
            conn.close()
            return False
        
        old_status = order_data[0]
        user_id = order_data[1]
        session_id = order_data[2]
        
        # Если заказ был выдан, возвращаем лимит
        if old_status == 'completed':
            cursor.execute("""
                SELECT SUM(quantity) FROM order_items WHERE order_id = ?
            """, (order_id,))
            total_boxes = cursor.fetchone()[0] or 0
            
            if total_boxes > 0:
                cursor.execute("""
                    UPDATE user_session_limits 
                    SET boxes_purchased = boxes_purchased - ?
                    WHERE user_id = ? AND session_id = ?
                """, (total_boxes, user_id, session_id))
        
        # Возвращаем количество ящиков товара
        cursor.execute("""
            SELECT product_id, quantity FROM order_items WHERE order_id = ?
        """, (order_id,))
        items = cursor.fetchall()
        
        for product_id, quantity in items:
            cursor.execute("""
                UPDATE products 
                SET boxes_count = boxes_count + ? 
                WHERE product_id = ?
            """, (quantity, product_id))
        
        # Удаляем товары заказа
        cursor.execute("DELETE FROM order_items WHERE order_id = ?", (order_id,))
        
        # Удаляем сам заказ
        cursor.execute("DELETE FROM orders WHERE order_id = ?", (order_id,))
        
        conn.commit()
        conn.close()
        logger.info(f"Заказ {order_id} удален")
        return True
    except Exception as e:
        logger.error(f"Ошибка при удалении заказа: {e}")
        conn.rollback()
        conn.close()
        return False


def get_session_orders(session_id: int) -> list:
    """Получает все заказы для сессии"""
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("""
        SELECT o.order_id, o.order_number, o.session_order_number, o.user_id, o.phone_number, o.full_name, 
               o.total_amount, o.status, o.created_at,
               GROUP_CONCAT(p.product_name || ' x' || oi.quantity || ' (' || oi.price || '₽)') as items
        FROM orders o
        LEFT JOIN order_items oi ON o.order_id = oi.order_id
        LEFT JOIN products p ON oi.product_id = p.product_id
        WHERE o.session_id = ?
        GROUP BY o.order_id
        ORDER BY o.session_order_number ASC, o.created_at DESC
    """, (session_id,))
    orders = cursor.fetchall()
    conn.close()
    return [
        {
            "order_id": order[0],
            "order_number": order[1],
            "session_order_number": order[2],
            "user_id": order[3],
            "phone_number": order[4],
            "full_name": order[5],
            "total_amount": order[6],
            "status": order[7],
            "created_at": order[8],
            "items": order[9] or "Нет товаров"
        }
        for order in orders
    ]


def get_session_sales_stats(session_id: int) -> dict:
    """Получает статистику продаж по сессии"""
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    
    # Общее количество заказов
    cursor.execute("SELECT COUNT(*) FROM orders WHERE session_id = ?", (session_id,))
    total_orders = cursor.fetchone()[0] or 0
    
    # Заказы по статусам
    cursor.execute("""
        SELECT status, COUNT(*) 
        FROM orders 
        WHERE session_id = ?
        GROUP BY status
    """, (session_id,))
    status_counts = {row[0]: row[1] for row in cursor.fetchall()}
    
    completed_orders = status_counts.get('completed', 0)
    processing_orders = status_counts.get('processing', 0)
    pending_orders = status_counts.get('pending', 0)
    cancelled_orders = status_counts.get('cancelled', 0)
    
    # Общая выручка (только выданные заказы)
    cursor.execute("""
        SELECT COALESCE(SUM(total_amount), 0)
        FROM orders
        WHERE session_id = ? AND status = 'completed'
    """, (session_id,))
    total_revenue = cursor.fetchone()[0] or 0
    
    # Всего продано ящиков (только выданные заказы)
    cursor.execute("""
        SELECT COALESCE(SUM(oi.quantity), 0)
        FROM orders o
        JOIN order_items oi ON o.order_id = oi.order_id
        WHERE o.session_id = ? AND o.status = 'completed'
    """, (session_id,))
    total_boxes_sold = cursor.fetchone()[0] or 0
    
    # Уникальных клиентов
    cursor.execute("""
        SELECT COUNT(DISTINCT user_id)
        FROM orders
        WHERE session_id = ?
    """, (session_id,))
    unique_customers = cursor.fetchone()[0] or 0
    
    # Получаем информацию о товарах сессии с проданными количествами
    cursor.execute("""
        SELECT 
            p.product_id,
            p.product_name,
            p.price,
            p.boxes_count,
            COALESCE(SUM(CASE WHEN o.status = 'completed' THEN oi.quantity ELSE 0 END), 0) as sold_boxes
        FROM products p
        LEFT JOIN order_items oi ON p.product_id = oi.product_id
        LEFT JOIN orders o ON oi.order_id = o.order_id AND o.session_id = ?
        WHERE p.session_id = ?
        GROUP BY p.product_id, p.product_name, p.price, p.boxes_count
        ORDER BY p.created_at DESC
    """, (session_id, session_id))
    
    products_info = []
    for row in cursor.fetchall():
        product_id, product_name, price, boxes_count, sold_boxes = row
        products_info.append({
            'product_id': product_id,
            'product_name': product_name,
            'price': price,
            'initial_boxes': boxes_count + sold_boxes,  # Начальное количество = текущее + проданное
            'sold_boxes': sold_boxes,
            'remaining_boxes': boxes_count
        })
    
    conn.close()
    
    return {
        'total_orders': total_orders,
        'completed_orders': completed_orders,
        'processing_orders': processing_orders,
        'pending_orders': pending_orders,
        'cancelled_orders': cancelled_orders,
        'total_revenue': total_revenue,
        'total_boxes_sold': total_boxes_sold,
        'unique_customers': unique_customers,
        'products': products_info
    }


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


def get_user_all_orders(user_id: int) -> list:
    """Получает все заказы пользователя по всем сессиям"""
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("""
        SELECT o.order_id, o.order_number, o.session_order_number, o.session_id, o.total_amount, o.status, o.created_at,
               s.session_name,
               GROUP_CONCAT(p.product_name || ' x' || oi.quantity || ' (' || oi.price || '₽)') as items
        FROM orders o
        LEFT JOIN sessions s ON o.session_id = s.session_id
        LEFT JOIN order_items oi ON o.order_id = oi.order_id
        LEFT JOIN products p ON oi.product_id = p.product_id
        WHERE o.user_id = ?
        GROUP BY o.order_id
        ORDER BY o.created_at DESC
    """, (user_id,))
    orders = cursor.fetchall()
    conn.close()
    return [
        {
            "order_id": order[0],
            "order_number": order[1],
            "session_order_number": order[2],
            "session_id": order[3],
            "total_amount": order[4],
            "status": order[5],
            "created_at": order[6],
            "session_name": order[7] or "Неизвестная сессия",
            "items": order[8] or "Нет товаров"
        }
        for order in orders
    ]


def get_user_pending_orders(user_id: int) -> list:
    """Получает все незавершенные заказы пользователя по всем сессиям"""
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("""
        SELECT o.order_id, o.order_number, o.session_order_number, o.session_id, o.total_amount, o.status, o.created_at,
               s.session_name,
               GROUP_CONCAT(p.product_name || ' x' || oi.quantity || ' (' || oi.price || '₽)') as items
        FROM orders o
        LEFT JOIN sessions s ON o.session_id = s.session_id
        LEFT JOIN order_items oi ON o.order_id = oi.order_id
        LEFT JOIN products p ON oi.product_id = p.product_id
        WHERE o.user_id = ? AND o.status != 'completed' AND o.status != 'cancelled'
        GROUP BY o.order_id
        ORDER BY o.created_at DESC
    """, (user_id,))
    orders = cursor.fetchall()
    conn.close()
    return [
        {
            "order_id": order[0],
            "order_number": order[1],
            "session_order_number": order[2],
            "session_id": order[3],
            "total_amount": order[4],
            "status": order[5],
            "created_at": order[6],
            "session_name": order[7] or "Неизвестная сессия",
            "items": order[8] or "Нет товаров"
        }
        for order in orders
    ]


def get_user_statistics(user_id: int) -> dict:
    """Получает статистику пользователя"""
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    
    # Общее количество купленных ящиков (только выданные заказы)
    cursor.execute("""
        SELECT COALESCE(SUM(oi.quantity), 0)
        FROM orders o
        JOIN order_items oi ON o.order_id = oi.order_id
        WHERE o.user_id = ? AND o.status = 'completed'
    """, (user_id,))
    total_boxes = cursor.fetchone()[0] or 0
    
    # Общая сумма выданных заказов
    cursor.execute("""
        SELECT COALESCE(SUM(total_amount), 0)
        FROM orders
        WHERE user_id = ? AND status = 'completed'
    """, (user_id,))
    total_amount = cursor.fetchone()[0] or 0
    
    # Количество выданных заказов
    cursor.execute("""
        SELECT COUNT(*)
        FROM orders
        WHERE user_id = ? AND status = 'completed'
    """, (user_id,))
    completed_orders = cursor.fetchone()[0] or 0
    
    # Количество незавершенных заказов
    cursor.execute("""
        SELECT COUNT(*)
        FROM orders
        WHERE user_id = ? AND status != 'completed' AND status != 'cancelled'
    """, (user_id,))
    pending_orders = cursor.fetchone()[0] or 0
    
    conn.close()
    
    return {
        "total_boxes": total_boxes,
        "total_amount": total_amount,
        "completed_orders": completed_orders,
        "pending_orders": pending_orders
    }


def get_users_with_pending_orders_by_session(session_id: int) -> list:
    """Получает список уникальных пользователей с не выданными заказами в сессии"""
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("""
        SELECT DISTINCT o.user_id
        FROM orders o
        WHERE o.session_id = ? 
        AND o.status != 'completed' 
        AND o.status != 'cancelled'
    """, (session_id,))
    user_ids = [row[0] for row in cursor.fetchall()]
    conn.close()
    return user_ids


def get_users_with_active_orders_by_session(session_id: int) -> list:
    """Получает список уникальных пользователей с активными заказами (pending или processing) в сессии"""
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("""
        SELECT DISTINCT o.user_id
        FROM orders o
        WHERE o.session_id = ? 
        AND (o.status = 'pending' OR o.status = 'processing')
    """, (session_id,))
    user_ids = [row[0] for row in cursor.fetchall()]
    conn.close()
    return user_ids
