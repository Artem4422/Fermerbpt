import database
import sqlite3

# ID пользователя для добавления в администраторы и менеджеры
USER_ID = 806966850

# Инициализируем базу данных
database.init_database()

# Проверяем, существует ли пользователь в таблице users
conn = sqlite3.connect(database.DB_NAME)
cursor = conn.cursor()
cursor.execute("SELECT user_id FROM users WHERE user_id = ?", (USER_ID,))
user_exists = cursor.fetchone()

if not user_exists:
    # Создаем минимальную запись пользователя
    cursor.execute("""
        INSERT OR IGNORE INTO users (user_id, first_name, chat_id)
        VALUES (?, ?, ?)
    """, (USER_ID, "Admin", USER_ID))
    conn.commit()
    print(f"Создана запись пользователя {USER_ID}")

conn.close()

# Добавляем администратора
if database.add_admin(USER_ID):
    print(f"Пользователь {USER_ID} успешно добавлен в администраторы!")
else:
    # Проверяем, может быть уже администратор
    if database.is_admin(USER_ID):
        print(f"Пользователь {USER_ID} уже является администратором.")
    else:
        print(f"Ошибка при добавлении пользователя {USER_ID} в администраторы.")

# Добавляем менеджера
if database.add_manager(USER_ID):
    print(f"Пользователь {USER_ID} успешно добавлен в менеджеры!")
else:
    # Проверяем, может быть уже менеджер
    if database.is_manager(USER_ID):
        print(f"Пользователь {USER_ID} уже является менеджером.")
    else:
        print(f"Ошибка при добавлении пользователя {USER_ID} в менеджеры.")
