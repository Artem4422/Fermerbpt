from telegram import InlineKeyboardButton, InlineKeyboardMarkup


def get_order_qr_keyboard(order_number: str) -> InlineKeyboardMarkup:
    """Создает клавиатуру с кнопкой для получения QR-кода заказа"""
    keyboard = [
        [InlineKeyboardButton("📱 Получить QR-код", callback_data=f"get_qr_{order_number}")],
        [InlineKeyboardButton("🔙 Назад", callback_data="cart_back")]
    ]
    return InlineKeyboardMarkup(keyboard)


def get_cart_orders_keyboard(session_id: int, orders: list) -> InlineKeyboardMarkup:
    """Создает клавиатуру с заказами в корзине и их QR-кодами"""
    keyboard = []
    for order in orders:
        keyboard.append([
            InlineKeyboardButton(
                f"Заказ #{order['order_number']} - QR",
                callback_data=f"get_qr_{order['order_number']}"
            )
        ])
    
    keyboard.append([InlineKeyboardButton("🔙 Назад к товарам", callback_data=f"session_{session_id}")])
    return InlineKeyboardMarkup(keyboard)
