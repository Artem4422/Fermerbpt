from telegram import InlineKeyboardButton, InlineKeyboardMarkup


def get_main_keyboard() -> InlineKeyboardMarkup:
    """Создает главную клавиатуру с кнопками Купить и Личный кабинет"""
    keyboard = [
        [InlineKeyboardButton("🛒 Купить", callback_data="main_buy")],
        [InlineKeyboardButton("👤 Личный кабинет", callback_data="main_cabinet")]
    ]
    return InlineKeyboardMarkup(keyboard)
