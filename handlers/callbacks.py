from telegram import Update
from telegram.ext import ContextTypes
import database
import config
import sqlite3
import logging

logger = logging.getLogger(__name__)


async def handle_admin_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Обработчик callback кнопок админ-панели и пользовательских действий"""
    query = update.callback_query
    user_id = update.effective_user.id
    
    await query.answer()
    
    callback_data = query.data
    
    # Обработка пользовательских действий (не требуют прав администратора)
    if callback_data.startswith("session_"):
        # Обработка выбора сессии пользователем
        session_id = int(callback_data.split("_")[1])
        session = database.get_session(session_id)
        if session:
            # Проверяем статус торговли для этой сессии
            if not database.is_session_trading_active(session_id):
                await query.edit_message_text(
                    f"⛔ Торговля закрыта\n\n"
                    f"Сессия: {session['session_name']}\n\n"
                    f"Торговля для этой сессии временно приостановлена. Попробуйте позже."
                )
                return
            
            # Получаем товары для этой сессии
            from keyboards.products import get_products_keyboard
            products_keyboard = get_products_keyboard(session_id)
            products = database.get_products_by_session(session_id)
            
            if products:
                products_text = "\n".join([
                    f"• {p['product_name']} - {p['price']}₽ (ящиков: {p['boxes_count']})"
                    for p in products
                ])
                await query.edit_message_text(
                    f"✅ Вы выбрали сессию: {session['session_name']}\n\n"
                    f"Доступные товары:\n{products_text}",
                    reply_markup=products_keyboard
                )
            else:
                await query.edit_message_text(
                    f"✅ Вы выбрали сессию: {session['session_name']}\n\n"
                    f"Товары пока не добавлены.",
                    reply_markup=products_keyboard
                )
        else:
            await query.answer("❌ Сессия не найдена!", show_alert=True)
        return
    
    elif callback_data.startswith("product_"):
        # Обработка выбора товара пользователем
        product_id = int(callback_data.split("_")[1])
        product = database.get_product(product_id)
        
        if product:
            session_id = product['session_id']
            session = database.get_session(session_id)
            
            # Проверяем статус торговли
            if not database.is_session_trading_active(session_id):
                await query.answer("⛔ Торговля для этой сессии закрыта!", show_alert=True)
                return
            
            # Получаем лимит и доступное количество
            limit = database.get_limit_per_person()
            purchased = database.get_user_session_boxes_purchased(user_id, session_id)
            available = database.get_user_available_boxes(user_id, session_id, product_id)
            
            from keyboards.products import get_product_info_keyboard
            keyboard = get_product_info_keyboard(product_id, session_id)
            
            limit_text = f"{limit} ящиков" if limit > 0 else "без ограничений"
            available_text = f"{available} ящиков" if available > 0 else "0 ящиков"
            
            await query.edit_message_text(
                f"📦 {product['product_name']}\n\n"
                f"💰 Цена: {product['price']}₽ за ящик\n"
                f"📊 Доступно ящиков: {product['boxes_count']}\n"
                f"👤 Ваш лимит: {limit_text}\n"
                f"✅ Куплено в этой сессии: {purchased} ящиков\n"
                f"🛒 Доступно для покупки: {available_text}",
                reply_markup=keyboard
            )
        else:
            await query.answer("❌ Товар не найден!", show_alert=True)
        return
    
    elif callback_data.startswith("buy_"):
        # Начало покупки товара
        product_id = int(callback_data.split("_")[1])
        product = database.get_product(product_id)
        
        if product:
            session_id = product['session_id']
            available = database.get_user_available_boxes(user_id, session_id, product_id)
            max_boxes = available
            
            if max_boxes <= 0:
                await query.answer("❌ Нет доступных ящиков для покупки!", show_alert=True)
                return
            
            from keyboards.products import get_quantity_keyboard
            keyboard = get_quantity_keyboard(product_id, max_boxes)
            
            await query.edit_message_text(
                f"🛒 Покупка: {product['product_name']}\n\n"
                f"💰 Цена за ящик: {product['price']}₽\n"
                f"📊 Максимум доступно: {max_boxes} ящиков\n\n"
                f"Выберите количество ящиков:",
                reply_markup=keyboard
            )
        else:
            await query.answer("❌ Товар не найден!", show_alert=True)
        return
    
    elif callback_data.startswith("qty_"):
        # Выбор количества ящиков
        parts = callback_data.split("_")
        product_id = int(parts[1])
        quantity = int(parts[2])
        
        product = database.get_product(product_id)
        
        if product:
            session_id = product['session_id']
            available = database.get_user_available_boxes(user_id, session_id, product_id)
            
            if quantity > available:
                await query.answer("❌ Недостаточно доступных ящиков!", show_alert=True)
                return
            
            total_cost = quantity * product['price']
            
            # Сохраняем данные покупки
            context.user_data['purchase'] = {
                'product_id': product_id,
                'session_id': session_id,
                'quantity': quantity,
                'price': product['price'],
                'total_cost': total_cost
            }
            
            from keyboards.products import get_confirm_phone_keyboard
            keyboard = get_confirm_phone_keyboard(product_id, quantity)
            
            await query.edit_message_text(
                f"🛒 Подтверждение покупки\n\n"
                f"Товар: {product['product_name']}\n"
                f"Количество: {quantity} ящиков\n"
                f"Цена за ящик: {product['price']}₽\n"
                f"💰 Общая стоимость: {total_cost}₽\n\n"
                f"Для продолжения подтвердите номер телефона:",
                reply_markup=keyboard
            )
        else:
            await query.answer("❌ Товар не найден!", show_alert=True)
        return
    
    elif callback_data.startswith("confirm_phone_"):
        # Подтверждение телефона
        parts = callback_data.split("_")
        product_id = int(parts[2])
        quantity = int(parts[3])
        
        if 'purchase' not in context.user_data:
            await query.answer("❌ Ошибка! Начните покупку заново.", show_alert=True)
            return
        
        # Запрашиваем номер телефона
        context.user_data['purchase']['step'] = 'phone'
        await query.edit_message_text(
            "📱 Подтверждение номера телефона\n\n"
            "Пожалуйста, отправьте ваш номер телефона текстом (например: +79991234567):"
        )
        return
    
    elif callback_data.startswith("cart_"):
        # Показ корзины пользователя
        session_id = int(callback_data.split("_")[1])
        session = database.get_session(session_id)
        
        if session:
            cart = database.get_user_cart(user_id, session_id)
            from keyboards.products import get_products_keyboard
            products_keyboard = get_products_keyboard(session_id)
            
            if cart:
                cart_text = "\n".join([
                    f"Заказ #{order['order_number']}\n"
                    f"Товары: {order['items']}\n"
                    f"Сумма: {order['total_amount']}₽\n"
                    f"Статус: {order['status']}\n"
                    for order in cart
                ])
                await query.edit_message_text(
                    f"🛒 Корзина - {session['session_name']}\n\n{cart_text}",
                    reply_markup=products_keyboard
                )
            else:
                await query.edit_message_text(
                    f"🛒 Корзина - {session['session_name']}\n\n"
                    f"Ваша корзина пуста.",
                    reply_markup=products_keyboard
                )
        else:
            await query.answer("❌ Сессия не найдена!", show_alert=True)
        return
    
    # Проверяем права администратора для админских действий
    if not database.is_admin(user_id):
        await query.answer("❌ У вас нет прав доступа!", show_alert=True)
        return
    
    # Обработка различных кнопок админ-панели
    if callback_data == "admin_add_session":
        # Запрашиваем имя сессии
        context.user_data['waiting_for_session_name'] = True
        await query.edit_message_text(
            "➕ Добавить сессию\n\n"
            "Введите имя новой сессии:"
        )
    
    elif callback_data == "admin_limit_per_person":
        # Запрашиваем лимит на человека
        context.user_data['waiting_for_limit_per_person'] = True
        current_limit = database.get_limit_per_person()
        limit_text = f"\nТекущий лимит: {current_limit} ящиков" if current_limit > 0 else ""
        await query.edit_message_text(
            f"👤 Лимит на человека{limit_text}\n\n"
            f"Какой лимит установить на одного человека?\n"
            f"Введите число (0 - без ограничений):"
        )
    
    elif callback_data == "admin_add_product":
        # Показываем список сессий для выбора
        from keyboards.sessions_admin import get_sessions_keyboard_for_admin
        sessions_keyboard = get_sessions_keyboard_for_admin("add_product")
        await query.edit_message_text(
            "➕ Добавить товар\n\n"
            "Выберите сессию для добавления товара:",
            reply_markup=sessions_keyboard
        )
    
    elif callback_data.startswith("admin_select_session_add_product_"):
        # Админ выбрал сессию для добавления товара
        session_id = int(callback_data.split("_")[-1])
        session = database.get_session(session_id)
        if session:
            context.user_data['adding_product'] = {
                'session_id': session_id,
                'step': 'name'
            }
            await query.edit_message_text(
                f"✅ Выбрана сессия: {session['session_name']}\n\n"
                f"Введите название товара:"
            )
        else:
            await query.answer("❌ Сессия не найдена!", show_alert=True)
    
    elif callback_data == "admin_delete_product":
        # Показываем список сессий для выбора
        from keyboards.sessions_admin import get_sessions_keyboard_for_admin
        sessions_keyboard = get_sessions_keyboard_for_admin("delete_product")
        await query.edit_message_text(
            "➖ Удалить товар\n\n"
            "Выберите сессию:",
            reply_markup=sessions_keyboard
        )
    
    elif callback_data.startswith("admin_select_session_delete_product_"):
        # Админ выбрал сессию для удаления товара
        session_id = int(callback_data.split("_")[-1])
        session = database.get_session(session_id)
        if session:
            products = database.get_products_by_session(session_id)
            if products:
                from keyboards.products_admin import get_products_keyboard_for_admin
                products_keyboard = get_products_keyboard_for_admin(session_id, "delete")
                await query.edit_message_text(
                    f"✅ Выбрана сессия: {session['session_name']}\n\n"
                    f"Выберите товар для удаления:",
                    reply_markup=products_keyboard
                )
            else:
                await query.edit_message_text(
                    f"✅ Выбрана сессия: {session['session_name']}\n\n"
                    f"В этой сессии нет товаров для удаления."
                )
        else:
            await query.answer("❌ Сессия не найдена!", show_alert=True)
    
    elif callback_data.startswith("admin_select_product_delete_"):
        # Админ выбрал товар для удаления
        product_id = int(callback_data.split("_")[-1])
        product = database.get_product(product_id)
        if product:
            from keyboards.products_admin import get_confirm_delete_keyboard
            confirm_keyboard = get_confirm_delete_keyboard(product_id)
            await query.edit_message_text(
                f"⚠️ Вы уверены, что хотите удалить товар?\n\n"
                f"Товар: {product['product_name']}\n"
                f"Цена: {product['price']}₽\n"
                f"Ящиков: {product['boxes_count']}",
                reply_markup=confirm_keyboard
            )
        else:
            await query.answer("❌ Товар не найден!", show_alert=True)
    
    elif callback_data.startswith("admin_confirm_delete_"):
        # Подтверждение удаления товара
        product_id = int(callback_data.split("_")[-1])
        product = database.get_product(product_id)
        if product:
            product_name = product['product_name']
            if database.delete_product(product_id):
                await query.edit_message_text(
                    f"✅ Товар '{product_name}' успешно удален!"
                )
            else:
                await query.edit_message_text(
                    f"❌ Ошибка при удалении товара!"
                )
        else:
            await query.answer("❌ Товар не найден!", show_alert=True)
    
    elif callback_data == "admin_start_trading":
        # Показываем список сессий для запуска торговли
        from keyboards.sessions_admin import get_sessions_keyboard_for_admin
        sessions_keyboard = get_sessions_keyboard_for_admin("start_trading")
        await query.edit_message_text(
            "▶️ Старт торги\n\n"
            "Выберите сессию для запуска торговли:",
            reply_markup=sessions_keyboard
        )
    
    elif callback_data == "admin_stop_trading":
        # Показываем список сессий для остановки торговли
        from keyboards.sessions_admin import get_sessions_keyboard_for_admin
        sessions_keyboard = get_sessions_keyboard_for_admin("stop_trading")
        await query.edit_message_text(
            "⏹️ Стоп торги\n\n"
            "Выберите сессию для остановки торговли:",
            reply_markup=sessions_keyboard
        )
    
    elif callback_data.startswith("admin_select_session_start_trading_"):
        # Админ выбрал сессию для запуска торговли
        session_id = int(callback_data.split("_")[-1])
        session = database.get_session(session_id)
        if session:
            if database.set_session_trading_status(session_id, True):
                await query.edit_message_text(
                    f"✅ Торговля для сессии '{session['session_name']}' успешно запущена!\n\n"
                    f"Теперь пользователи могут выбирать товары из этой сессии."
                )
            else:
                await query.edit_message_text(
                    f"❌ Ошибка при запуске торговли для сессии '{session['session_name']}'!"
                )
        else:
            await query.answer("❌ Сессия не найдена!", show_alert=True)
    
    elif callback_data.startswith("admin_select_session_stop_trading_"):
        # Админ выбрал сессию для остановки торговли
        session_id = int(callback_data.split("_")[-1])
        session = database.get_session(session_id)
        if session:
            if database.set_session_trading_status(session_id, False):
                await query.edit_message_text(
                    f"✅ Торговля для сессии '{session['session_name']}' успешно остановлена!\n\n"
                    f"Пользователи больше не могут выбирать товары из этой сессии."
                )
            else:
                await query.edit_message_text(
                    f"❌ Ошибка при остановке торговли для сессии '{session['session_name']}'!"
                )
        else:
            await query.answer("❌ Сессия не найдена!", show_alert=True)
    
    elif callback_data == "admin_change_box_volume":
        await query.edit_message_text("📦 Изменить объем ящика\n\nФункция в разработке...")
    
    elif callback_data == "admin_change_order":
        await query.edit_message_text("📋 Изменить заказ\n\nФункция в разработке...")
    
    elif callback_data == "admin_payment_status":
        await query.edit_message_text("💳 Статус оплаты\n\nФункция в разработке...")
    
    elif callback_data == "admin_sales_status":
        await query.edit_message_text("📊 Статус продаж\n\nФункция в разработке...")
    
    elif callback_data == "admin_add_admin":
        await query.edit_message_text("👑 Назначить администратора\n\nФункция в разработке...")
    
    elif callback_data == "admin_remove_admin":
        await query.edit_message_text("🔻 Снять администратора\n\nФункция в разработке...")
    
    elif callback_data == "admin_add_manager":
        # Запрашиваем ID пользователя для добавления менеджера
        context.user_data['waiting_for_manager_id'] = True
        await query.edit_message_text(
            "👔 Добавить менеджера\n\n"
            "Введите ID пользователя, которого хотите назначить менеджером:"
        )
    
    elif callback_data == "admin_remove_manager":
        # Показываем список менеджеров для удаления
        conn = sqlite3.connect(database.DB_NAME)
        cursor = conn.cursor()
        cursor.execute("""
            SELECT m.user_id, u.first_name, u.username
            FROM managers m
            JOIN users u ON m.user_id = u.user_id
        """)
        managers = cursor.fetchall()
        conn.close()
        
        if managers:
            from keyboards.managers_admin import get_managers_keyboard
            managers_keyboard = get_managers_keyboard("remove")
            managers_text = "\n".join([
                f"• {m[1]} (@{m[2] if m[2] else 'нет'}) - ID: {m[0]}"
                for m in managers
            ])
            await query.edit_message_text(
                f"🔻 Снять менеджера\n\n"
                f"Выберите менеджера для удаления:\n\n{managers_text}",
                reply_markup=managers_keyboard
            )
        else:
            await query.edit_message_text("❌ Менеджеры не найдены!")
    
    elif callback_data.startswith("admin_remove_manager_"):
        # Удаление менеджера
        manager_id = int(callback_data.split("_")[-1])
        if database.remove_manager(manager_id):
            await query.edit_message_text(f"✅ Менеджер с ID {manager_id} успешно удален!")
        else:
            await query.edit_message_text(f"❌ Ошибка при удалении менеджера!")
    
    elif callback_data == "admin_reports":
        await query.edit_message_text("📈 Отчеты\n\nФункция в разработке...")
    
    elif callback_data == "admin_close_session":
        await query.edit_message_text("✅ Сессия закрыта")
    
    elif callback_data == "admin_back":
        # Возврат к главной админ-панели
        from keyboards.admin import get_admin_keyboard
        await query.edit_message_text(
            "🔹 Админ-панель 🔹\n\n"
            "Выберите необходимое действие:",
            reply_markup=get_admin_keyboard()
        )
    
    # Обработчики панели менеджера
    elif callback_data == "manager_find_order":
        # Запрос номера заказа
        context.user_data['waiting_for_order_number'] = True
        await query.edit_message_text(
            "🔍 Найти заказ\n\n"
            "Введите номер заказа:"
        )
    
    elif callback_data == "manager_back":
        # Возврат к панели менеджера
        from keyboards.manager import get_manager_keyboard
        await query.edit_message_text(
            "👔 Панель менеджера 👔\n\n"
            "Выберите необходимое действие:",
            reply_markup=get_manager_keyboard()
        )
    
    elif callback_data.startswith("manager_order_"):
        # Показ информации о заказе
        order_id = int(callback_data.split("_")[-1])
        order = database.get_order(order_id)
        if order:
            order_items = database.get_order_items(order_id)
            session = database.get_session(order['session_id'])
            
            items_text = "\n".join([
                f"• {item['product_name']} x{item['quantity']} = {item['quantity'] * item['price']}₽"
                for item in order_items
            ])
            
            from keyboards.manager import get_order_actions_keyboard
            keyboard = get_order_actions_keyboard(order_id)
            
            await query.edit_message_text(
                f"📋 Заказ #{order['order_number']}\n\n"
                f"📦 Сессия: {session['session_name'] if session else 'Не найдена'}\n"
                f"👤 ФИО: {order['full_name']}\n"
                f"📱 Телефон: {order['phone_number']}\n"
                f"📊 Статус: {database.get_order_status_ru(order['status'])}\n"
                f"📅 Дата: {order['created_at']}\n\n"
                f"Товары:\n{items_text}\n\n"
                f"💰 Общая сумма: {order['total_amount']}₽",
                reply_markup=keyboard
            )
        else:
            await query.answer("❌ Заказ не найден!", show_alert=True)
    
    elif callback_data.startswith("manager_edit_order_"):
        # Показ меню изменения статуса
        order_id = int(callback_data.split("_")[-1])
        from keyboards.manager import get_order_status_keyboard
        keyboard = get_order_status_keyboard(order_id)
        await query.edit_message_text(
            "✏️ Изменить статус заказа\n\n"
            "Выберите новый статус:",
            reply_markup=keyboard
        )
    
    elif callback_data.startswith("manager_status_"):
        # Изменение статуса заказа
        parts = callback_data.split("_")
        status = parts[2]
        order_id = int(parts[3])
        
        order = database.get_order(order_id)
        if order:
            if database.update_order_status(order_id, status):
                # Отправляем уведомление пользователю
                try:
                    status_text = database.get_order_status_ru(status)
                    
                    if status == 'completed':
                        message_text = (
                            f"✅ Ваш заказ #{order['order_number']} выдан!\n\n"
                            f"Спасибо за покупку!"
                        )
                    else:
                        message_text = (
                            f"📋 Статус вашего заказа #{order['order_number']} изменен:\n"
                            f"{status_text}"
                        )
                    
                    await context.bot.send_message(
                        chat_id=order['user_id'],
                        text=message_text
                    )
                except Exception as e:
                    logger.error(f"Ошибка при отправке уведомления: {e}")
                
                await query.edit_message_text(
                    f"✅ Статус заказа #{order['order_number']} успешно изменен на: {database.get_order_status_ru(status)}"
                )
            else:
                await query.edit_message_text("❌ Ошибка при изменении статуса заказа!")
        else:
            await query.answer("❌ Заказ не найден!", show_alert=True)
    
    elif callback_data.startswith("manager_decline_order_"):
        # Отклонение заказа
        order_id = int(callback_data.split("_")[-1])
        order = database.get_order(order_id)
        if order:
            if database.update_order_status(order_id, 'cancelled'):
                await query.edit_message_text(f"✅ Заказ #{order['order_number']} отклонен!")
            else:
                await query.edit_message_text("❌ Ошибка при отклонении заказа!")
        else:
            await query.answer("❌ Заказ не найден!", show_alert=True)
    
    elif callback_data == "manager_report":
        # Выбор сессии для отчета
        from keyboards.sessions_admin import get_sessions_keyboard_for_admin
        sessions_keyboard = get_sessions_keyboard_for_admin("report")
        await query.edit_message_text(
            "📊 Отчет\n\n"
            "Выберите сессию для формирования отчета:",
            reply_markup=sessions_keyboard
        )
    
    elif callback_data.startswith("admin_select_session_report_"):
        # Генерация отчета для сессии
        session_id = int(callback_data.split("_")[-1])
        session = database.get_session(session_id)
        if session:
            orders = database.get_session_orders(session_id)
            
            # Генерируем текст отчета
            report_lines = []
            report_lines.append(f"ОТЧЕТ ПО СЕССИИ: {session['session_name']}")
            report_lines.append("")
            report_lines.append(f"Всего заказов: {len(orders)}")
            report_lines.append("")
            
            completed_count = sum(1 for o in orders if o['status'] == 'completed')
            pending_count = sum(1 for o in orders if o['status'] == 'pending')
            processing_count = sum(1 for o in orders if o['status'] == 'processing')
            cancelled_count = sum(1 for o in orders if o['status'] == 'cancelled')
            
            report_lines.append(f"Выдано: {completed_count}")
            report_lines.append(f"Ожидает обработки: {pending_count}")
            report_lines.append(f"В обработке: {processing_count}")
            report_lines.append(f"Отменено: {cancelled_count}")
            report_lines.append("")
            report_lines.append("=" * 60)
            report_lines.append("")
            
            for order in orders:
                report_lines.append(f"Заказ #{order['order_number']}")
                report_lines.append(f"ФИО: {order['full_name']}")
                report_lines.append(f"Телефон: {order['phone_number']}")
                report_lines.append(f"Статус: {database.get_order_status_ru(order['status'])}")
                report_lines.append(f"Товары: {order['items']}")
                report_lines.append(f"Сумма: {order['total_amount']}₽")
                report_lines.append(f"Дата: {order['created_at']}")
                report_lines.append("-" * 60)
                report_lines.append("")
            
            report_text = "\n".join(report_lines)
            
            # Генерируем изображение отчета
            try:
                from PIL import Image, ImageDraw, ImageFont
                import io
                
                # Создаем изображение
                img_width = 1000
                line_height = 25
                padding = 20
                img_height = len(report_lines) * line_height + padding * 2
                
                img = Image.new('RGB', (img_width, img_height), color='white')
                draw = ImageDraw.Draw(img)
                
                try:
                    font = ImageFont.truetype("arial.ttf", 14)
                except:
                    try:
                        font = ImageFont.truetype("C:/Windows/Fonts/arial.ttf", 14)
                    except:
                        font = ImageFont.load_default()
                
                y = padding
                for line in report_lines:
                    # Обрезаем длинные строки
                    if len(line) > 80:
                        line = line[:77] + "..."
                    draw.text((padding, y), line, fill='black', font=font)
                    y += line_height
                
                # Сохраняем в байты
                img_bytes = io.BytesIO()
                img.save(img_bytes, format='PNG')
                img_bytes.seek(0)
                
                await query.message.reply_photo(
                    photo=img_bytes,
                    caption=f"📊 Отчет по сессии: {session['session_name']}"
                )
                await query.edit_message_text("✅ Отчет успешно сформирован!")
            except Exception as e:
                logger.error(f"Ошибка при генерации изображения: {e}")
                # Если не удалось создать изображение, отправляем текстовый отчет
                await query.edit_message_text(
                    f"📊 Отчет по сессии: {session['session_name']}\n\n{report_text[:4000]}"
                )
        else:
            await query.answer("❌ Сессия не найдена!", show_alert=True)
