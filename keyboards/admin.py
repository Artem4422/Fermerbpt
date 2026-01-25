from telegram import InlineKeyboardButton, InlineKeyboardMarkup


def get_admin_keyboard() -> InlineKeyboardMarkup:
    """Создает клавиатуру админ-панели"""
    keyboard = [
        # Сессии
        [
            InlineKeyboardButton("Добавить сессию", callback_data="admin_add_session"),
            InlineKeyboardButton("Лимит на чел", callback_data="admin_limit_per_person")
        ],
        # Товары
        [
            InlineKeyboardButton("Добавить товар", callback_data="admin_add_product"),
            InlineKeyboardButton("Удалить товар", callback_data="admin_delete_product")
        ],
        # Торговля
        [
            InlineKeyboardButton("Старт торги", callback_data="admin_start_trading"),
            InlineKeyboardButton("Стоп торги", callback_data="admin_stop_trading")
        ],
        # Редактирование
        [
            InlineKeyboardButton("Изм.объема ящ", callback_data="admin_change_box_volume"),
            InlineKeyboardButton("Изменить заказ", callback_data="admin_change_order")
        ],
        # Статистика и отчеты
        [
            InlineKeyboardButton("Статус продаж", callback_data="admin_sales_status"),
            InlineKeyboardButton("Отчеты", callback_data="admin_reports")
        ],
        # Администраторы
        [
            InlineKeyboardButton("Назначить администратора", callback_data="admin_add_admin"),
            InlineKeyboardButton("Снять администратора", callback_data="admin_remove_admin")
        ],
        # Менеджеры
        [
            InlineKeyboardButton("Добавить менеджера", callback_data="admin_add_manager"),
            InlineKeyboardButton("Снять менеджера", callback_data="admin_remove_manager")
        ],
        # Закрытие сессии
        [
            InlineKeyboardButton("Закрыть сессию", callback_data="admin_close_session"),
            InlineKeyboardButton("Статус продаж", callback_data="admin_sales_status")
        ]
    ]
    
    return InlineKeyboardMarkup(keyboard)
