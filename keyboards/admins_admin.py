from telegram import InlineKeyboardButton, InlineKeyboardMarkup
import sqlite3
import database


def get_admins_keyboard(action: str) -> InlineKeyboardMarkup:
    """Создает клавиатуру с администраторами"""
    conn = sqlite3.connect(database.DB_NAME)
    cursor = conn.cursor()
    cursor.execute("""
        SELECT a.user_id, u.first_name
        FROM admins a
        JOIN users u ON a.user_id = u.user_id
    """)
    admins = cursor.fetchall()
    conn.close()
    
    keyboard = []
    for admin_id, first_name in admins:
        if action == "remove":
            keyboard.append([
                InlineKeyboardButton(
                    f"{first_name} (ID: {admin_id})",
                    callback_data=f"admin_remove_admin_{admin_id}"
                )
            ])
    
    keyboard.append([InlineKeyboardButton("🔙 Назад", callback_data="admin_back")])
    return InlineKeyboardMarkup(keyboard)
