from telegram import InlineKeyboardButton, InlineKeyboardMarkup
import sqlite3
import database


def get_managers_keyboard(action: str) -> InlineKeyboardMarkup:
    """Создает клавиатуру с менеджерами"""
    conn = sqlite3.connect(database.DB_NAME)
    cursor = conn.cursor()
    cursor.execute("""
        SELECT m.user_id, u.first_name
        FROM managers m
        JOIN users u ON m.user_id = u.user_id
    """)
    managers = cursor.fetchall()
    conn.close()
    
    keyboard = []
    for manager_id, first_name in managers:
        if action == "remove":
            keyboard.append([
                InlineKeyboardButton(
                    f"{first_name} (ID: {manager_id})",
                    callback_data=f"admin_remove_manager_{manager_id}"
                )
            ])
    
    keyboard.append([InlineKeyboardButton("🔙 Назад", callback_data="admin_back")])
    return InlineKeyboardMarkup(keyboard)
