from telegram import InlineKeyboardButton, InlineKeyboardMarkup
import database


def get_products_keyboard_for_admin(session_id: int, action: str = "delete") -> InlineKeyboardMarkup:
    """Создает клавиатуру с кнопками товаров для администратора при удалении"""
    products = database.get_products_by_session(session_id)
    
    if not products:
        # Если товаров нет, возвращаем только кнопку "Назад"
        keyboard = [[InlineKeyboardButton("🔙 Назад", callback_data="admin_back")]]
        return InlineKeyboardMarkup(keyboard)
    
    keyboard = []
    # Создаем кнопки по 2 в ряд
    for i in range(0, len(products), 2):
        row = []
        product = products[i]
        button_text = f"{product['product_name']} - {product['price']}₽"
        
        # Специальная обработка для добавления товара в заказ
        if action.startswith("add_to_order_"):
            order_id = action.split("_")[-1]
            callback_data = f"admin_select_product_add_to_order_{product['product_id']}_{order_id}"
        else:
            callback_data = f"admin_select_product_{action}_{product['product_id']}"
        
        row.append(InlineKeyboardButton(
            button_text,
            callback_data=callback_data
        ))
        if i + 1 < len(products):
            product2 = products[i + 1]
            button_text2 = f"{product2['product_name']} - {product2['price']}₽"
            
            if action.startswith("add_to_order_"):
                order_id = action.split("_")[-1]
                callback_data2 = f"admin_select_product_add_to_order_{product2['product_id']}_{order_id}"
            else:
                callback_data2 = f"admin_select_product_{action}_{product2['product_id']}"
            
            row.append(InlineKeyboardButton(
                button_text2,
                callback_data=callback_data2
            ))
        keyboard.append(row)
    
    # Добавляем кнопку "Назад"
    if action.startswith("add_to_order_"):
        order_id = action.split("_")[-1]
        keyboard.append([InlineKeyboardButton("🔙 Назад", callback_data=f"admin_edit_order_items_{order_id}")])
    else:
        keyboard.append([InlineKeyboardButton("🔙 Назад", callback_data="admin_back")])
    
    return InlineKeyboardMarkup(keyboard)


def get_confirm_delete_keyboard(product_id: int) -> InlineKeyboardMarkup:
    """Создает клавиатуру подтверждения удаления товара"""
    keyboard = [
        [
            InlineKeyboardButton("✅ Да", callback_data=f"admin_confirm_delete_{product_id}"),
            InlineKeyboardButton("❌ Нет", callback_data="admin_back")
        ]
    ]
    return InlineKeyboardMarkup(keyboard)
