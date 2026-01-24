from telegram import InlineKeyboardButton, InlineKeyboardMarkup
import database


def get_sessions_keyboard() -> InlineKeyboardMarkup:
    """Создает клавиатуру с кнопками сессий"""
    sessions = database.get_all_sessions()
    
    if not sessions:
        # Если сессий нет, возвращаем пустую клавиатуру
        return InlineKeyboardMarkup([])
    
    keyboard = []
    # Создаем кнопки по 2 в ряд
    for i in range(0, len(sessions), 2):
        row = []
        row.append(InlineKeyboardButton(
            sessions[i]["session_name"],
            callback_data=f"session_{sessions[i]['session_id']}"
        ))
        if i + 1 < len(sessions):
            row.append(InlineKeyboardButton(
                sessions[i + 1]["session_name"],
                callback_data=f"session_{sessions[i + 1]['session_id']}"
            ))
        keyboard.append(row)
    
    return InlineKeyboardMarkup(keyboard)
