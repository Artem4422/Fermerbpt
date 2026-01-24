from telegram import InlineKeyboardButton, InlineKeyboardMarkup


def get_back_to_products_keyboard(session_id: int) -> InlineKeyboardMarkup:
    """Создает клавиатуру с кнопкой возврата к товарам"""
    keyboard = [
        [InlineKeyboardButton("🛒 Вернуться к покупкам", callback_data=f"session_{session_id}")]
    ]
    return InlineKeyboardMarkup(keyboard)
