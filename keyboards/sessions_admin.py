from telegram import InlineKeyboardButton, InlineKeyboardMarkup
import database


def get_sessions_keyboard_for_admin(action: str = "select") -> InlineKeyboardMarkup:
    """Создает клавиатуру с кнопками сессий для администратора"""
    sessions = database.get_all_sessions()
    
    if not sessions:
        # Если сессий нет, возвращаем пустую клавиатуру
        return InlineKeyboardMarkup([])
    
    keyboard = []
    # Создаем кнопки по 2 в ряд
    for i in range(0, len(sessions), 2):
        row = []
        # Для отчета используем специальный callback
        if action == "report":
            callback_prefix = "admin_select_session_report_"
        else:
            callback_prefix = f"admin_select_session_{action}_"
        
        row.append(InlineKeyboardButton(
            sessions[i]["session_name"],
            callback_data=f"{callback_prefix}{sessions[i]['session_id']}"
        ))
        if i + 1 < len(sessions):
            row.append(InlineKeyboardButton(
                sessions[i + 1]["session_name"],
                callback_data=f"{callback_prefix}{sessions[i + 1]['session_id']}"
            ))
        keyboard.append(row)
    
    # Добавляем кнопку "Назад"
    if action == "report":
        keyboard.append([InlineKeyboardButton("🔙 Назад", callback_data="manager_back")])
    else:
        keyboard.append([InlineKeyboardButton("🔙 Назад", callback_data="admin_back")])
    
    return InlineKeyboardMarkup(keyboard)
