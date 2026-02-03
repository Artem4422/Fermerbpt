from telegram import InlineKeyboardButton, InlineKeyboardMarkup


def get_reports_type_keyboard() -> InlineKeyboardMarkup:
    """Создает клавиатуру выбора типа отчета"""
    keyboard = [
        [InlineKeyboardButton("📅 Отчет за период", callback_data="admin_report_period")],
        [InlineKeyboardButton("📊 Отчет по сессии", callback_data="admin_report_session")],
        [InlineKeyboardButton("📺 Отчет для канала", callback_data="admin_channel_report")],
        [InlineKeyboardButton("📋 Полный отчет (2 столбца)", callback_data="admin_full_data_report")],
        [InlineKeyboardButton("🔙 Назад", callback_data="admin_back")]
    ]
    return InlineKeyboardMarkup(keyboard)


def get_reports_period_keyboard() -> InlineKeyboardMarkup:
    """Создает клавиатуру выбора периода для отчета"""
    keyboard = [
        [InlineKeyboardButton("📅 Отчет за неделю", callback_data="admin_report_week")],
        [InlineKeyboardButton("📅 Отчет за месяц", callback_data="admin_report_month")],
        [InlineKeyboardButton("📅 Отчет за год", callback_data="admin_report_year")],
        [InlineKeyboardButton("📅 Отчет за все время", callback_data="admin_report_all_time")],
        [InlineKeyboardButton("🔙 Назад", callback_data="admin_reports")]
    ]
    return InlineKeyboardMarkup(keyboard)


def get_manager_reports_type_keyboard() -> InlineKeyboardMarkup:
    """Создает клавиатуру выбора типа отчета для менеджера"""
    keyboard = [
        [InlineKeyboardButton("📋 Таблица не выданных", callback_data="manager_pending_table")],
        [InlineKeyboardButton("📋 Список заказов", callback_data="manager_full_data_report")],
        [InlineKeyboardButton("🔙 Назад", callback_data="manager_back")]
    ]
    return InlineKeyboardMarkup(keyboard)


def get_manager_reports_period_keyboard() -> InlineKeyboardMarkup:
    """Создает клавиатуру выбора периода для отчета менеджера"""
    keyboard = [
        [InlineKeyboardButton("📅 Отчет за неделю", callback_data="manager_report_week")],
        [InlineKeyboardButton("📅 Отчет за месяц", callback_data="manager_report_month")],
        [InlineKeyboardButton("📅 Отчет за год", callback_data="manager_report_year")],
        [InlineKeyboardButton("📅 Отчет за все время", callback_data="manager_report_all_time")],
        [InlineKeyboardButton("🔙 Назад", callback_data="manager_reports")]
    ]
    return InlineKeyboardMarkup(keyboard)
