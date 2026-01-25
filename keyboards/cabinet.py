from telegram import InlineKeyboardButton, InlineKeyboardMarkup
import database


def get_cabinet_keyboard() -> InlineKeyboardMarkup:
    """Создает клавиатуру личного кабинета"""
    keyboard = [
        [InlineKeyboardButton("🛒 Корзина", callback_data="cabinet_cart")],
        [InlineKeyboardButton("🔙 Главное меню", callback_data="main_menu")]
    ]
    return InlineKeyboardMarkup(keyboard)


def get_cart_sessions_keyboard(orders: list) -> InlineKeyboardMarkup:
    """Создает клавиатуру с сессиями, в которых есть незавершенные заказы"""
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
    
    keyboard.append([InlineKeyboardButton("🔙 Назад", callback_data="main_cabinet")])
    return InlineKeyboardMarkup(keyboard)


def get_cart_orders_keyboard(session_id: int, orders: list) -> InlineKeyboardMarkup:
    """Создает клавиатуру с заказами в корзине для конкретной сессии"""
    keyboard = []
    for order in orders:
        keyboard.append([
            InlineKeyboardButton(
                f"Заказ #{order['order_number']} - {database.get_order_status_ru(order['status'])}",
                callback_data=f"cabinet_order_{order['order_id']}"
            )
        ])
    
    keyboard.append([InlineKeyboardButton("🔙 Назад к корзине", callback_data="cabinet_cart")])
    return InlineKeyboardMarkup(keyboard)
