from telegram import InlineKeyboardButton, InlineKeyboardMarkup
import database


def get_products_keyboard(session_id: int) -> InlineKeyboardMarkup:
    """Создает клавиатуру с кнопками товаров для сессии"""
    products = database.get_products_by_session(session_id)
    
    keyboard = []
    if products:
        # Создаем кнопки по 2 в ряд
        for i in range(0, len(products), 2):
            row = []
            product = products[i]
            button_text = f"{product['product_name']} - {product['price']}₽"
            row.append(InlineKeyboardButton(
                button_text,
                callback_data=f"product_{product['product_id']}"
            ))
            if i + 1 < len(products):
                product2 = products[i + 1]
                button_text2 = f"{product2['product_name']} - {product2['price']}₽"
                row.append(InlineKeyboardButton(
                    button_text2,
                    callback_data=f"product_{product2['product_id']}"
                ))
            keyboard.append(row)
    
    # Кнопка корзины и всегда «В начало» внизу
    keyboard.append([InlineKeyboardButton("🛒 Корзина", callback_data=f"cart_{session_id}")])
    keyboard.append([InlineKeyboardButton("🔙 В начало", callback_data="main_menu")])
    
    return InlineKeyboardMarkup(keyboard)


def get_product_info_keyboard(product_id: int, session_id: int) -> InlineKeyboardMarkup:
    """Создает клавиатуру для информации о товаре. Всегда есть «В начало» внизу."""
    keyboard = [
        [InlineKeyboardButton("🛒 Купить", callback_data=f"buy_{product_id}")],
        [InlineKeyboardButton("🔙 Назад к товарам", callback_data=f"session_{session_id}")],
        [InlineKeyboardButton("🔙 В начало", callback_data="main_menu")]
    ]
    return InlineKeyboardMarkup(keyboard)


def get_quantity_keyboard(product_id: int, max_quantity: int) -> InlineKeyboardMarkup:
    """Создает клавиатуру для выбора количества ящиков. Всегда есть «В начало» внизу."""
    keyboard = []
    quantities = [1, 2, 3, 5, 10]
    row = []
    for qty in quantities:
        if qty <= max_quantity:
            row.append(InlineKeyboardButton(str(qty), callback_data=f"qty_{product_id}_{qty}"))
            if len(row) == 2:
                keyboard.append(row)
                row = []
    if row:
        keyboard.append(row)
    
    keyboard.append([InlineKeyboardButton("🔙 Назад", callback_data=f"product_{product_id}")])
    keyboard.append([InlineKeyboardButton("🔙 В начало", callback_data="main_menu")])
    
    return InlineKeyboardMarkup(keyboard)


def get_confirm_phone_keyboard(product_id: int, quantity: int) -> InlineKeyboardMarkup:
    """Создает клавиатуру подтверждения телефона. Всегда есть «В начало» внизу."""
    keyboard = [
        [InlineKeyboardButton("✅ Подтвердить номер телефона", callback_data=f"confirm_phone_{product_id}_{quantity}")],
        [InlineKeyboardButton("🔙 Назад", callback_data=f"buy_{product_id}")],
        [InlineKeyboardButton("🔙 В начало", callback_data="main_menu")]
    ]
    return InlineKeyboardMarkup(keyboard)
