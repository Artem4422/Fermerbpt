from telegram import InlineKeyboardButton, InlineKeyboardMarkup


def get_manager_keyboard() -> InlineKeyboardMarkup:
    """Создает клавиатуру панели менеджера"""
    keyboard = [
        [InlineKeyboardButton("🔍 Найти", callback_data="manager_find_order")],
        [InlineKeyboardButton("📊 Отчет", callback_data="manager_report")]
    ]
    return InlineKeyboardMarkup(keyboard)


def get_order_actions_keyboard(order_id: int) -> InlineKeyboardMarkup:
    """Создает клавиатуру действий с заказом"""
    keyboard = [
        [InlineKeyboardButton("✏️ Изменить", callback_data=f"manager_edit_order_{order_id}")],
        [InlineKeyboardButton("❌ Отклонить", callback_data=f"manager_decline_order_{order_id}")],
        [InlineKeyboardButton("🔙 Назад", callback_data="manager_back")]
    ]
    return InlineKeyboardMarkup(keyboard)


def get_order_status_keyboard(order_id: int) -> InlineKeyboardMarkup:
    """Создает клавиатуру для изменения статуса заказа"""
    keyboard = [
        [InlineKeyboardButton("✅ Выдан", callback_data=f"manager_status_completed_{order_id}")],
        [InlineKeyboardButton("⏳ В обработке", callback_data=f"manager_status_processing_{order_id}")],
        [InlineKeyboardButton("❌ Отменен", callback_data=f"manager_status_cancelled_{order_id}")],
        [InlineKeyboardButton("🔙 Назад", callback_data=f"manager_order_{order_id}")]
    ]
    return InlineKeyboardMarkup(keyboard)
