from telegram import InlineKeyboardButton, InlineKeyboardMarkup


def get_admin_keyboard() -> InlineKeyboardMarkup:
    """Создает клавиатуру админ-панели"""
    keyboard = [
        [
            InlineKeyboardButton("Добавить сессию", callback_data="admin_add_session"),
            InlineKeyboardButton("Лимит на чел", callback_data="admin_limit_per_person")
        ],
        [
            InlineKeyboardButton("Добавить товар", callback_data="admin_add_product"),
            InlineKeyboardButton("Удалить товар", callback_data="admin_delete_product")
        ],
        [
            InlineKeyboardButton("Старт торги", callback_data="admin_start_trading"),
            InlineKeyboardButton("Стоп торги", callback_data="admin_stop_trading")
        ],
        [
            InlineKeyboardButton("Изм.объема ящ", callback_data="admin_change_box_volume"),
            InlineKeyboardButton("Изменить заказ", callback_data="admin_change_order")
        ],
        [
            InlineKeyboardButton("Статус оплаты", callback_data="admin_payment_status"),
            InlineKeyboardButton("Статус продаж", callback_data="admin_sales_status")
        ],
        [
            InlineKeyboardButton("Назначить администратора", callback_data="admin_add_admin"),
            InlineKeyboardButton("Снять администратора", callback_data="admin_remove_admin")
        ],
        [
            InlineKeyboardButton("Добавить менеджера", callback_data="admin_add_manager"),
            InlineKeyboardButton("Снять менеджера", callback_data="admin_remove_manager")
        ],
        [
            InlineKeyboardButton("Отчеты", callback_data="admin_reports"),
            InlineKeyboardButton("Закрыть сессию", callback_data="admin_close_session")
        ]
    ]
    
    return InlineKeyboardMarkup(keyboard)
