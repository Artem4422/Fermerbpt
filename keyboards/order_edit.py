from telegram import InlineKeyboardButton, InlineKeyboardMarkup


def get_order_edit_keyboard(order_id: int) -> InlineKeyboardMarkup:
    """Создает клавиатуру для редактирования заказа"""
    keyboard = [
        [InlineKeyboardButton("✏️ Изменить состав и количество", callback_data=f"admin_edit_order_items_{order_id}")],
        [InlineKeyboardButton("🗑️ Удалить заказ", callback_data=f"admin_delete_order_{order_id}")],
        [InlineKeyboardButton("🔙 Назад", callback_data="admin_back")]
    ]
    return InlineKeyboardMarkup(keyboard)


def get_confirm_delete_order_keyboard(order_id: int) -> InlineKeyboardMarkup:
    """Создает клавиатуру подтверждения удаления заказа"""
    keyboard = [
        [
            InlineKeyboardButton("✅ Да, удалить", callback_data=f"admin_confirm_delete_order_{order_id}"),
            InlineKeyboardButton("❌ Нет", callback_data=f"admin_order_{order_id}")
        ]
    ]
    return InlineKeyboardMarkup(keyboard)
