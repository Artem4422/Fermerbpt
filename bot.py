import logging
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, CallbackQueryHandler, filters
import config
import database
from handlers import commands, callbacks, messages

# Настройка логирования
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Инициализируем базу данных при запуске
database.init_database()


def main() -> None:
    """Запуск бота"""
    # Создаем приложение
    application = Application.builder().token(config.BOT_TOKEN).build()

    # Регистрируем обработчики команд
    application.add_handler(CommandHandler("start", commands.start))
    application.add_handler(CommandHandler("help", commands.help_command))
    application.add_handler(CommandHandler("status", commands.status))
    application.add_handler(CommandHandler("admin", commands.admin_panel))
    application.add_handler(CommandHandler("panel", commands.manager_panel))

    # Регистрируем обработчик callback кнопок
    application.add_handler(CallbackQueryHandler(callbacks.handle_admin_callback, pattern="^admin_"))

    # Регистрируем обработчик текстовых сообщений
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, messages.handle_message))
    
    # Регистрируем обработчик фото (для сканирования QR-кодов)
    application.add_handler(MessageHandler(filters.PHOTO, messages.handle_photo))
    
    # Регистрируем обработчик callback для сессий
    application.add_handler(CallbackQueryHandler(callbacks.handle_admin_callback, pattern="^session_"))
    
    # Регистрируем обработчики callback для покупок
    application.add_handler(CallbackQueryHandler(callbacks.handle_admin_callback, pattern="^product_"))
    application.add_handler(CallbackQueryHandler(callbacks.handle_admin_callback, pattern="^buy_"))
    application.add_handler(CallbackQueryHandler(callbacks.handle_admin_callback, pattern="^qty_"))
    application.add_handler(CallbackQueryHandler(callbacks.handle_admin_callback, pattern="^confirm_phone_"))
    application.add_handler(CallbackQueryHandler(callbacks.handle_admin_callback, pattern="^cart_"))
    
    # Регистрируем обработчики callback для панели менеджера
    application.add_handler(CallbackQueryHandler(callbacks.handle_admin_callback, pattern="^manager_"))
    application.add_handler(CallbackQueryHandler(callbacks.handle_admin_callback, pattern="^admin_select_session_report_"))
    application.add_handler(CallbackQueryHandler(callbacks.handle_admin_callback, pattern="^admin_remove_manager_"))
    application.add_handler(CallbackQueryHandler(callbacks.handle_admin_callback, pattern="^admin_remove_admin_"))
    
    # Регистрируем обработчик для получения QR-кода
    application.add_handler(CallbackQueryHandler(callbacks.handle_admin_callback, pattern="^get_qr_"))
    
    # Регистрируем обработчики для редактирования заказов
    application.add_handler(CallbackQueryHandler(callbacks.handle_admin_callback, pattern="^admin_order_"))
    application.add_handler(CallbackQueryHandler(callbacks.handle_admin_callback, pattern="^admin_edit_order_items_"))
    application.add_handler(CallbackQueryHandler(callbacks.handle_admin_callback, pattern="^admin_delete_order_"))
    application.add_handler(CallbackQueryHandler(callbacks.handle_admin_callback, pattern="^admin_confirm_delete_order_"))
    application.add_handler(CallbackQueryHandler(callbacks.handle_admin_callback, pattern="^admin_edit_item_"))
    application.add_handler(CallbackQueryHandler(callbacks.handle_admin_callback, pattern="^admin_delete_item_"))
    application.add_handler(CallbackQueryHandler(callbacks.handle_admin_callback, pattern="^admin_add_item_to_order_"))
    application.add_handler(CallbackQueryHandler(callbacks.handle_admin_callback, pattern="^admin_select_product_add_to_order_"))

    # Запускаем бота
    logger.info("Бот запущен...")
    application.run_polling(allowed_updates=Update.ALL_TYPES)


if __name__ == '__main__':
    main()
