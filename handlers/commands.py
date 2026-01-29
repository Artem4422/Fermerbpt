from telegram import Update
from telegram.ext import ContextTypes
import database


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Обработчик команды /start"""
    user = update.effective_user
    chat_id = update.effective_chat.id
    
    # Сохраняем всю информацию о пользователе в базу данных
    database.save_or_update_user(user, chat_id)
    
    # Админы и менеджеры не проходят регистрацию
    if database.is_admin(user.id) or database.is_manager(user.id):
        from keyboards.main import get_main_keyboard
        await update.message.reply_text(
            "Привет, я бот-фермер, готов помочь тебе!",
            reply_markup=get_main_keyboard()
        )
        return
    
    # Проверяем, зарегистрирован ли пользователь (есть ли телефон)
    if not database.is_registered(user.id):
        context.user_data['registering'] = {'step': 'phone'}
        await update.message.reply_text(
            "👋 Добро пожаловать!\n\n"
            "Для использования бота нужно пройти регистрацию.\n\n"
            "📱 Введите ваш номер телефона (например: +79991234567):"
        )
        return
    
    # Уже зарегистрирован — показываем главное меню
    from keyboards.main import get_main_keyboard
    await update.message.reply_text(
        "Привет, я бот-фермер, готов помочь тебе!",
        reply_markup=get_main_keyboard()
    )


async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Обработчик команды /help"""
    help_text = """
Доступные команды:
/start - Начать работу с ботом
/help - Показать это сообщение
/status - Проверить статус бота
/admin - Админ-панель (только для администраторов)
    """
    await update.message.reply_text(help_text)


async def status(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Обработчик команды /status"""
    await update.message.reply_text("✅ Бот работает нормально!")


async def admin_panel(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Обработчик команды /admin"""
    user_id = update.effective_user.id
    
    # Проверяем права администратора
    if not database.is_admin(user_id):
        await update.message.reply_text("❌ У вас нет прав доступа к админ-панели!")
        return
    
    # Импортируем клавиатуру админ-панели
    from keyboards.admin import get_admin_keyboard
    
    await update.message.reply_text(
        "🔹 Админ-панель 🔹\n\n"
        "Выберите необходимое действие:",
        reply_markup=get_admin_keyboard()
    )


async def manager_panel(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Обработчик команды /panel"""
    user_id = update.effective_user.id
    
    # Проверяем права менеджера
    if not database.is_manager(user_id):
        await update.message.reply_text("❌ У вас нет прав доступа к панели менеджера!")
        return
    
    # Импортируем клавиатуру панели менеджера
    from keyboards.manager import get_manager_keyboard
    
    await update.message.reply_text(
        "👔 Панель менеджера 👔\n\n"
        "Выберите необходимое действие:",
        reply_markup=get_manager_keyboard()
    )
