from telegram import InlineKeyboardButton, InlineKeyboardMarkup
import database


def get_cabinet_keyboard() -> InlineKeyboardMarkup:
    """Создает клавиатуру личного кабинета"""
    keyboard = [
        [InlineKeyboardButton("✏️ Изменить телефон и ФИО", callback_data="cabinet_edit_profile")],
        [InlineKeyboardButton("🛒 Корзина", callback_data="cabinet_cart")],
        [InlineKeyboardButton("🔙 Главное меню", callback_data="main_menu")]
    ]
    return InlineKeyboardMarkup(keyboard)


def get_cart_sessions_keyboard(orders: list, back_callback: str = "main_cabinet") -> InlineKeyboardMarkup:
    """Создает клавиатуру с сессиями, в которых есть заказы"""
    keyboard = []
    
    # Группируем заказы по сессиям
    sessions_dict = {}
    for order in orders:
        session_id = order['session_id']
        if session_id not in sessions_dict:
            sessions_dict[session_id] = {
                'session_name': order['session_name'],
                'orders': []
            }
        sessions_dict[session_id]['orders'].append(order)
    
    # Создаем кнопки для каждой сессии
    for session_id, session_data in sessions_dict.items():
        orders_count = len(session_data['orders'])
        keyboard.append([
            InlineKeyboardButton(
                f"📦 {session_data['session_name']} ({orders_count} заказов)",
                callback_data=f"cabinet_cart_session_{session_id}"
            )
        ])
    
    keyboard.append([InlineKeyboardButton("🔙 Назад", callback_data=back_callback)])
    return InlineKeyboardMarkup(keyboard)


def get_cart_orders_keyboard(session_id: int, orders: list, back_callback: str = "cabinet_cart") -> InlineKeyboardMarkup:
    """Создает клавиатуру с заказами для конкретной сессии"""
    keyboard = []
    for order in orders:
        # Показываем код заказа и номер из таблицы (номер по сессии)
        order_code = order['order_number']
        table_number = order.get('session_order_number', '—')
        # Заменяем "Ожидает обработки" на "Активен"
        status_display = database.get_order_status_ru(order['status'])
        if status_display == "Ожидает обработки":
            status_display = "Активен"
        keyboard.append([
            InlineKeyboardButton(
                f"Заказ №{table_number} (код: {order_code}) - {status_display}",
                callback_data=f"cabinet_order_{order['order_id']}"
            )
        ])
    
    keyboard.append([InlineKeyboardButton("🔙 Назад", callback_data=back_callback)])
    return InlineKeyboardMarkup(keyboard)
