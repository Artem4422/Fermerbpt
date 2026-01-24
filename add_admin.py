import database
import sqlite3

# ID пользователя для добавления в администраторы
ADMIN_USER_ID = 7952860005

# Инициализируем базу данных
database.init_database()

# Проверяем, существует ли пользователь в таблице users
conn = sqlite3.connect(database.DB_NAME)
cursor = conn.cursor()
cursor.execute("SELECT user_id FROM users WHERE user_id = ?", (ADMIN_USER_ID,))
user_exists = cursor.fetchone()

if not user_exists:
    # Создаем минимальную запись пользователя
    cursor.execute("""
        INSERT OR IGNORE INTO users (user_id, first_name, chat_id)
        VALUES (?, ?, ?)
    """, (ADMIN_USER_ID, "Admin", ADMIN_USER_ID))
    conn.commit()
    print(f"Создана запись пользователя {ADMIN_USER_ID}")

conn.close()

# Добавляем администратора
if database.add_admin(ADMIN_USER_ID):
    print(f"Пользователь {ADMIN_USER_ID} успешно добавлен в администраторы!")
else:
    # Проверяем, может быть уже администратор
    if database.is_admin(ADMIN_USER_ID):
        print(f"Пользователь {ADMIN_USER_ID} уже является администратором.")
    else:
        print(f"Ошибка при добавлении пользователя {ADMIN_USER_ID} в администраторы.")
