from telegram import InlineKeyboardButton, InlineKeyboardMarkup


def get_order_items_edit_keyboard(order_id: int, order_items: list) -> InlineKeyboardMarkup:
    """Создает клавиатуру для редактирования товаров в заказе"""
    keyboard = []
    
    for item in order_items:
        keyboard.append([
            InlineKeyboardButton(
                f"✏️ {item['product_name']} x{item['quantity']}",
                callback_data=f"admin_edit_item_{order_id}_{item['item_id']}"
            )
        ])
        keyboard.append([
            InlineKeyboardButton(
                f"🗑️ Удалить {item['product_name']}",
                callback_data=f"admin_delete_item_{order_id}_{item['item_id']}"
            )
        ])
    
    keyboard.append([InlineKeyboardButton("➕ Добавить товар", callback_data=f"admin_add_item_to_order_{order_id}")])
    keyboard.append([InlineKeyboardButton("🔙 Назад", callback_data=f"admin_order_{order_id}")])
    
    return InlineKeyboardMarkup(keyboard)
