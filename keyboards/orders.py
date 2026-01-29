from telegram import InlineKeyboardButton, InlineKeyboardMarkup


def get_back_to_products_keyboard(session_id: int) -> InlineKeyboardMarkup:
    """Создает клавиатуру после покупки. Всегда есть «В начало» внизу."""
    keyboard = [
        [InlineKeyboardButton("🛒 Вернуться к покупкам", callback_data=f"session_{session_id}")],
        [InlineKeyboardButton("🔙 В начало", callback_data="main_menu")]
    ]
    return InlineKeyboardMarkup(keyboard)
