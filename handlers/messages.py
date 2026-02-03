from telegram import Update
from telegram.ext import ContextTypes
import database
import io


async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Обработчик текстовых сообщений"""
    user_id = update.effective_user.id
    
    # Регистрация: телефон и ФИО
    if context.user_data.get('registering'):
        reg = context.user_data['registering']
        step = reg.get('step')
        text = update.message.text.strip()
        
        if step == 'phone':
            if len(text) > 0:
                reg['phone_number'] = text
                reg['step'] = 'full_name'
                await update.message.reply_text(
                    f"✅ Номер телефона сохранён.\n\n"
                    f"Введите ваше ФИО (Фамилия Имя Отчество):"
                )
            else:
                await update.message.reply_text("❌ Введите номер телефона.")
            return
        
        if step == 'full_name':
            if len(text) > 0:
                database.update_user_profile(
                    user_id,
                    phone_number=reg.get('phone_number'),
                    full_name=text
                )
                context.user_data.pop('registering', None)
                from keyboards.main import get_main_keyboard
                await update.message.reply_text(
                    "✅ Регистрация завершена! Теперь вы можете пользоваться ботом.",
                    reply_markup=get_main_keyboard()
                )
            else:
                await update.message.reply_text("❌ Введите ФИО.")
            return
    
    # Редактирование профиля (телефон и ФИО) из личного кабинета
    if context.user_data.get('editing_profile'):
        ed = context.user_data['editing_profile']
        step = ed.get('step')
        text = update.message.text.strip()
        
        if step == 'phone':
            if len(text) > 0:
                ed['phone_number'] = text
                ed['step'] = 'full_name'
                await update.message.reply_text(
                    "✅ Телефон сохранён.\n\nВведите ваше ФИО (Фамилия Имя Отчество):"
                )
            else:
                await update.message.reply_text("❌ Введите номер телефона.")
            return
        
        if step == 'full_name':
            if len(text) > 0:
                database.update_user_profile(
                    user_id,
                    phone_number=ed.get('phone_number'),
                    full_name=text
                )
                context.user_data.pop('editing_profile', None)
                stats = database.get_user_statistics(user_id)
                info = database.get_user_info(user_id)
                phone = (info or {}).get('phone_number') or '—'
                full_name_display = (info or {}).get('full_name') or '—'
                from keyboards.cabinet import get_cabinet_keyboard
                await update.message.reply_text(
                    f"✅ Контакты обновлены!\n\n"
                    f"👤 Личный кабинет\n\n"
                    f"📱 Телефон: {phone}\n"
                    f"👤 ФИО: {full_name_display}\n\n"
                    f"📊 Статистика:\n"
                    f"• Куплено ящиков: {stats['total_boxes']}\n"
                    f"• Выдано заказов: {stats['completed_orders']}\n"
                    f"• Ожидает обработки: {stats['pending_orders']}\n"
                    f"• Общая сумма: {stats['total_amount']:.2f}₽",
                    reply_markup=get_cabinet_keyboard()
                )
            else:
                await update.message.reply_text("❌ Введите ФИО.")
            return
    
    # Проверяем, ожидаем ли мы имя сессии от администратора (шаг 1)
    if context.user_data.get('waiting_for_session_name'):
        if database.is_admin(user_id):
            session_name = update.message.text.strip()
            if len(session_name) > 0:
                context.user_data['waiting_for_session_name'] = False
                context.user_data['creating_session'] = {'session_name': session_name}
                context.user_data['waiting_for_session_description'] = True
                await update.message.reply_text(
                    f"✅ Имя сессии: {session_name}\n\n"
                    "Введите описание сессии (можно ссылку или текст; при необходимости оставьте пустым и отправьте «-»):"
                )
            else:
                await update.message.reply_text("❌ Имя сессии не может быть пустым!")
        else:
            context.user_data['waiting_for_session_name'] = False
            await update.message.reply_text("❌ У вас нет прав для создания сессии!")
        return

    # Ожидаем описание сессии от администратора (шаг 2)
    if context.user_data.get('waiting_for_session_description'):
        if database.is_admin(user_id):
            creating = context.user_data.get('creating_session', {})
            session_name = creating.get('session_name', '')
            if not session_name:
                context.user_data.pop('waiting_for_session_description', None)
                context.user_data.pop('creating_session', None)
                await update.message.reply_text("❌ Сессия не создана: имя потеряно. Начните заново из админ-панели.")
                return
            raw = update.message.text.strip()
            description = "" if raw == "-" or not raw else raw
            context.user_data.pop('waiting_for_session_description', None)
            context.user_data.pop('creating_session', None)
            session_id = database.add_session(session_name, user_id, description)
            if session_id:
                desc_preview = f"\nОписание: {description}" if description else ""
                await update.message.reply_text(
                    f"✅ Сессия «{session_name}» успешно создана!{desc_preview}"
                )
            else:
                await update.message.reply_text(
                    "❌ Ошибка при создании сессии. Возможно, сессия с таким именем уже существует."
                )
        else:
            context.user_data.pop('waiting_for_session_description', None)
            context.user_data.pop('creating_session', None)
            await update.message.reply_text("❌ У вас нет прав для создания сессии!")
        return

    # Обработка добавления товара
    if context.user_data.get('adding_product'):
        if not database.is_admin(user_id):
            context.user_data.pop('adding_product', None)
            await update.message.reply_text("❌ У вас нет прав для добавления товара!")
            return
        
        product_data = context.user_data['adding_product']
        step = product_data.get('step')
        text = update.message.text.strip()
        
        if step == 'name':
            # Сохраняем название товара
            if len(text) > 0:
                product_data['product_name'] = text
                product_data['step'] = 'price'
                await update.message.reply_text(
                    f"✅ Название товара: {text}\n\n"
                    f"Введите цену товара (число):"
                )
            else:
                await update.message.reply_text("❌ Название товара не может быть пустым!")
        
        elif step == 'price':
            # Сохраняем цену товара
            try:
                price = float(text.replace(',', '.'))
                if price > 0:
                    product_data['price'] = price
                    product_data['step'] = 'boxes'
                    await update.message.reply_text(
                        f"✅ Цена товара: {price}₽\n\n"
                        f"Введите количество ящиков (число):"
                    )
                else:
                    await update.message.reply_text("❌ Цена должна быть больше нуля!")
            except ValueError:
                await update.message.reply_text("❌ Введите корректное число для цены!")
        
        elif step == 'boxes':
            # Сохраняем количество ящиков и добавляем товар
            try:
                boxes_count = int(text)
                if boxes_count >= 0:
                    product_id = database.add_product(
                        session_id=product_data['session_id'],
                        product_name=product_data['product_name'],
                        price=product_data['price'],
                        boxes_count=boxes_count,
                        created_by=user_id
                    )
                    
                    if product_id:
                        session = database.get_session(product_data['session_id'])
                        await update.message.reply_text(
                            f"✅ Товар успешно добавлен!\n\n"
                            f"Сессия: {session['session_name']}\n"
                            f"Товар: {product_data['product_name']}\n"
                            f"Цена: {product_data['price']}₽\n"
                            f"Ящиков: {boxes_count}"
                        )
                        context.user_data.pop('adding_product', None)
                    else:
                        await update.message.reply_text("❌ Ошибка при добавлении товара!")
                else:
                    await update.message.reply_text("❌ Количество ящиков не может быть отрицательным!")
            except ValueError:
                await update.message.reply_text("❌ Введите корректное целое число для количества ящиков!")
    
    # Обработка установки лимита на человека
    elif context.user_data.get('waiting_for_limit_per_person'):
        if database.is_admin(user_id):
            text = update.message.text.strip()
            try:
                limit = int(text)
                if limit >= 0:
                    if database.set_limit_per_person(limit):
                        context.user_data['waiting_for_limit_per_person'] = False
                        limit_text = f"{limit} ящиков" if limit > 0 else "без ограничений"
                        await update.message.reply_text(
                            f"✅ Лимит на одного человека успешно установлен: {limit_text}"
                        )
                    else:
                        await update.message.reply_text("❌ Ошибка при установке лимита!")
                else:
                    await update.message.reply_text("❌ Лимит не может быть отрицательным!")
            except ValueError:
                await update.message.reply_text("❌ Введите корректное целое число!")
        else:
            context.user_data['waiting_for_limit_per_person'] = False
            await update.message.reply_text("❌ У вас нет прав для установки лимита!")
    
    # Обработка покупки товара
    elif context.user_data.get('purchase'):
        purchase_data = context.user_data['purchase']
        step = purchase_data.get('step')
        text = update.message.text.strip()
        
        if step == 'phone':
            # Сохраняем номер телефона и запрашиваем ФИО
            if len(text) > 0:
                purchase_data['phone_number'] = text
                purchase_data['step'] = 'full_name'
                await update.message.reply_text(
                    f"✅ Номер телефона: {text}\n\n"
                    f"Введите ваше ФИО (Фамилия Имя Отчество):"
                )
            else:
                await update.message.reply_text("❌ Номер телефона не может быть пустым!")
        
        elif step == 'full_name':
            # Сохраняем ФИО и создаем заказ
            if len(text) > 0:
                purchase_data['full_name'] = text
                # Сохраняем телефон и ФИО в профиль для следующих покупок
                database.update_user_profile(
                    user_id,
                    phone_number=purchase_data.get('phone_number'),
                    full_name=text
                )
                
                # Создаем заказ
                order_id = database.create_order(
                    user_id=user_id,
                    session_id=purchase_data['session_id'],
                    phone_number=purchase_data['phone_number'],
                    full_name=purchase_data['full_name'],
                    items=[{
                        'product_id': purchase_data['product_id'],
                        'quantity': purchase_data['quantity'],
                        'price': purchase_data['price']
                    }]
                )
                
                if order_id:
                    order = database.get_order(order_id)
                    order_items = database.get_order_items(order_id)
                    product = database.get_product(purchase_data['product_id'])
                    session = database.get_session(purchase_data['session_id'])
                    
                    # Проверяем, остались ли лимиты
                    limit = database.get_limit_per_person()
                    purchased = database.get_user_session_boxes_purchased(user_id, purchase_data['session_id'])
                    available = limit - purchased if limit > 0 else 999999
                    
                    from keyboards.products import get_products_keyboard
                    products_keyboard = get_products_keyboard(purchase_data['session_id'])
                    
                    items_text = "\n".join([
                        f"• {item['product_name']} x{item['quantity']} = {item['quantity'] * item['price']}₽"
                        for item in order_items
                    ])
                    
                    continue_text = ""
                    back_keyboard = None
                    if limit == 0 or available > 0:
                        if limit > 0:
                            continue_text = f"\n\n✅ У вас осталось {available} ящиков для покупки в этой сессии."
                        else:
                            continue_text = f"\n\n✅ Вы можете продолжить покупки в этой сессии."
                        from keyboards.orders import get_back_to_products_keyboard
                        back_keyboard = get_back_to_products_keyboard(purchase_data['session_id'])
                    
                    # Генерируем и отправляем QR-код
                    import qr_code
                    qr_image = qr_code.generate_qr_code(order['order_number'])
                    
                    # Формируем номер заказа для отображения
                    table_number = order.get('session_order_number', '—')
                    order_code = order['order_number']
                    order_num_display = f"№{table_number} (код: {order_code})"
                    
                    await update.message.reply_photo(
                        photo=qr_image,
                        caption=(
                            f"✅ Заказ успешно создан!\n\n"
                            f"📋 Номер заказа: {order_num_display}\n"
                            f"📦 Сессия: {session['session_name']}\n"
                            f"👤 ФИО: {order['full_name']}\n"
                            f"📱 Телефон: {order['phone_number']}\n\n"
                            f"Товары:\n{items_text}\n\n"
                            f"💰 Общая сумма: {order['total_amount']}₽{continue_text}"
                        ),
                        reply_markup=back_keyboard if back_keyboard else products_keyboard
                    )
                    
                    # Очищаем данные покупки
                    context.user_data.pop('purchase', None)
                else:
                    await update.message.reply_text("❌ Ошибка при создании заказа!")
            else:
                await update.message.reply_text("❌ ФИО не может быть пустым!")
    
    # Обработка поиска заказа менеджером
    elif context.user_data.get('finding_order'):
        finding_data = context.user_data['finding_order']
        if finding_data.get('step') == 'waiting_number':
            if database.is_manager(user_id) or database.is_admin(user_id):
                session_id = finding_data['session_id']
                session = database.get_session(session_id)
                
                if not session:
                    context.user_data.pop('finding_order', None)
                    await update.message.reply_text("❌ Сессия не найдена!")
                    return
                
                order_number = update.message.text.strip()
                
                # Сначала пытаемся найти по номеру сессии в этой сессии
                order = None
                if order_number.isdigit():
                    # Ищем по номеру сессии в конкретной сессии
                    orders = database.find_orders_by_session_numbers(session_id, [int(order_number)])
                    if orders:
                        order = orders[0]
                
                # Если не найдено, ищем по общему номеру заказа
                if not order:
                    order = database.find_order_by_number(order_number)
                    # Проверяем, что заказ принадлежит выбранной сессии
                    if order and order['session_id'] != session_id:
                        order = None
                
                if order:
                    order_items = database.get_order_items(order['order_id'])
                    order_session = database.get_session(order['session_id'])
                    
                    items_text = "\n".join([
                        f"• {item['product_name']} x{item['quantity']} = {item['quantity'] * item['price']}₽"
                        for item in order_items
                    ])
                    
                    from keyboards.manager import get_order_actions_keyboard
                    keyboard = get_order_actions_keyboard(order['order_id'])
                    
                    order_num_display = f"#{order.get('session_order_number', order['order_number'])}"
                    if order.get('session_order_number'):
                        order_num_display += f" (общий: {order['order_number']})"
                    
                    await update.message.reply_text(
                        f"📋 Заказ {order_num_display}\n\n"
                        f"📦 Сессия: {order_session['session_name'] if order_session else 'Не найдена'}\n"
                        f"👤 ФИО: {order['full_name']}\n"
                        f"📱 Телефон: {order['phone_number']}\n"
                        f"📊 Статус: {database.get_order_status_ru(order['status'])}\n"
                        f"📅 Дата: {order['created_at']}\n\n"
                        f"Товары:\n{items_text}\n\n"
                        f"💰 Общая сумма: {order['total_amount']}₽",
                        reply_markup=keyboard
                    )
                    context.user_data.pop('finding_order', None)
                else:
                    await update.message.reply_text(
                        f"❌ Заказ с номером {order_number} не найден в сессии '{session['session_name']}'!\n\n"
                        f"Попробуйте еще раз или вернитесь в панель менеджера."
                    )
            else:
                context.user_data.pop('finding_order', None)
                await update.message.reply_text("❌ У вас нет прав для поиска заказов!")
    
    # Старый обработчик для обратной совместимости (если где-то остался)
    elif context.user_data.get('waiting_for_order_number'):
        if database.is_manager(user_id):
            order_number = update.message.text.strip()
            order = database.find_order_by_number(order_number)
            
            if order:
                order_items = database.get_order_items(order['order_id'])
                session = database.get_session(order['session_id'])
                
                items_text = "\n".join([
                    f"• {item['product_name']} x{item['quantity']} = {item['quantity'] * item['price']}₽"
                    for item in order_items
                ])
                
                from keyboards.manager import get_order_actions_keyboard
                keyboard = get_order_actions_keyboard(order['order_id'])
                
                order_num_display = f"#{order.get('session_order_number', order['order_number'])}"
                if order.get('session_order_number'):
                    order_num_display += f" (общий: {order['order_number']})"
                
                await update.message.reply_text(
                    f"📋 Заказ {order_num_display}\n\n"
                    f"📦 Сессия: {session['session_name'] if session else 'Не найдена'}\n"
                    f"👤 ФИО: {order['full_name']}\n"
                    f"📱 Телефон: {order['phone_number']}\n"
                    f"📊 Статус: {database.get_order_status_ru(order['status'])}\n"
                    f"📅 Дата: {order['created_at']}\n\n"
                    f"Товары:\n{items_text}\n\n"
                    f"💰 Общая сумма: {order['total_amount']}₽",
                    reply_markup=keyboard
                )
                context.user_data.pop('waiting_for_order_number', None)
            else:
                await update.message.reply_text(
                    f"❌ Заказ с номером {order_number} не найден!\n\n"
                    f"Попробуйте еще раз или вернитесь в панель менеджера."
                )
        else:
            context.user_data.pop('waiting_for_order_number', None)
            await update.message.reply_text("❌ У вас нет прав для поиска заказов!")
    
    # Обработка массовой выдачи заказов менеджером
    elif context.user_data.get('bulk_complete'):
        bulk_data = context.user_data['bulk_complete']
        if bulk_data.get('step') == 'waiting_numbers':
            if database.is_manager(user_id) or database.is_admin(user_id):
                session_id = bulk_data['session_id']
                session = database.get_session(session_id)
                
                if not session:
                    context.user_data.pop('bulk_complete', None)
                    await update.message.reply_text("❌ Сессия не найдена!")
                    return
                
                # Парсим номера заказов
                text = update.message.text.strip()
                try:
                    # Разбиваем строку на числа (поддерживаем и запятые, и пробелы)
                    # Заменяем запятые на пробелы и разбиваем
                    text_normalized = text.replace(',', ' ').replace('，', ' ').replace(';', ' ')  # Поддержка запятых, точки с запятой
                    order_numbers = [int(num.strip()) for num in text_normalized.split() if num.strip().isdigit()]
                    
                    if not order_numbers:
                        await update.message.reply_text(
                            "❌ Не найдено ни одного номера заказа!\n\n"
                            "Введите номера заказов через пробел или запятую (например: 1 11 2 3 5 или 1,2,3,4):"
                        )
                        return
                    
                    # Находим заказы по номерам сессии
                    orders = database.find_orders_by_session_numbers(session_id, order_numbers)
                    
                    if not orders:
                        await update.message.reply_text(
                            f"❌ Не найдено ни одного заказа с указанными номерами в сессии '{session['session_name']}'!\n\n"
                            f"Попробуйте еще раз."
                        )
                        return
                    
                    # Фильтруем только незавершенные заказы
                    pending_orders = [o for o in orders if o['status'] != 'completed']
                    already_completed = [o for o in orders if o['status'] == 'completed']
                    
                    if not pending_orders:
                        already_text = "\n".join([f"• Заказ №{o['session_order_number']}" for o in already_completed[:10]])
                        if len(already_completed) > 10:
                            already_text += f"\n... и еще {len(already_completed) - 10} заказов"
                        await update.message.reply_text(
                            f"⚠️ Все указанные заказы уже выданы!\n\n"
                            f"Уже выданные заказы:\n{already_text}"
                        )
                        context.user_data.pop('bulk_complete', None)
                        return
                    
                    # Выполняем массовую выдачу
                    order_ids = [o['order_id'] for o in pending_orders]
                    result = database.bulk_complete_orders(order_ids)
                    
                    # Формируем отчет
                    success_count = len(result['success'])
                    failed_count = len(result['failed'])
                    already_count = len(result['already_completed'])
                    
                    report_text = f"✅ Массовая выдача завершена!\n\n"
                    report_text += f"📦 Сессия: {session['session_name']}\n\n"
                    report_text += f"✅ Успешно выдано: {success_count} заказов\n"
                    
                    if already_count > 0:
                        report_text += f"⚠️ Уже были выданы: {already_count} заказов\n"
                    if failed_count > 0:
                        report_text += f"❌ Ошибка при выдаче: {failed_count} заказов\n"
                    
                    # Отправляем уведомления пользователям
                    for order_id in result['success']:
                        order = database.get_order(order_id)
                        if order:
                            try:
                                await context.bot.send_message(
                                    chat_id=order['user_id'],
                                    text=f"✅ Ваш заказ №{order.get('session_order_number', order['order_number'])} выдан!\n\n"
                                         f"Спасибо за покупку!"
                                )
                            except Exception as e:
                                import logging
                                logging.getLogger(__name__).error(f"Ошибка при отправке уведомления: {e}")
                    
                    # Показываем список выданных заказов
                    if success_count > 0:
                        success_orders = [o for o in pending_orders if o['order_id'] in result['success']]
                        orders_list = "\n".join([
                            f"• Заказ №{o['session_order_number']} - {o['full_name']}"
                            for o in success_orders[:20]
                        ])
                        if len(success_orders) > 20:
                            orders_list += f"\n... и еще {len(success_orders) - 20} заказов"
                        report_text += f"\n\nВыданные заказы:\n{orders_list}"
                    
                    await update.message.reply_text(report_text)
                    context.user_data.pop('bulk_complete', None)
                except ValueError:
                    await update.message.reply_text(
                        "❌ Некорректный формат!\n\n"
                        "Введите номера заказов через пробел или запятую (например: 1 11 2 3 5 или 1,2,3,4):"
                    )
            else:
                context.user_data.pop('bulk_complete', None)
                await update.message.reply_text("❌ У вас нет прав для массовой выдачи!")
    
    # Обработка оповещения не выданных заказов
    elif context.user_data.get('notify_pending'):
        notify_data = context.user_data['notify_pending']
        if notify_data.get('step') == 'waiting_message':
            if database.is_manager(user_id) or database.is_admin(user_id):
                session_id = notify_data['session_id']
                session = database.get_session(session_id)
                
                if not session:
                    context.user_data.pop('notify_pending', None)
                    await update.message.reply_text("❌ Сессия не найдена!")
                    return
                
                message_text = update.message.text.strip()
                
                if not message_text:
                    await update.message.reply_text(
                        "❌ Текст сообщения не может быть пустым!\n\n"
                        "Введите текст сообщения:"
                    )
                    return
                
                # Получаем пользователей с не выданными заказами
                user_ids = database.get_users_with_pending_orders_by_session(session_id)
                
                if not user_ids:
                    await update.message.reply_text(
                        f"❌ В сессии '{session['session_name']}' нет пользователей с не выданными заказами!"
                    )
                    context.user_data.pop('notify_pending', None)
                    return
                
                # Отправляем сообщения
                sent_count = 0
                failed_count = 0
                
                await update.message.reply_text(f"⏳ Отправка сообщений {len(user_ids)} пользователям...")
                
                for user_id in user_ids:
                    try:
                        await context.bot.send_message(
                            chat_id=user_id,
                            text=message_text
                        )
                        sent_count += 1
                    except Exception as e:
                        import logging
                        logging.getLogger(__name__).error(f"Ошибка при отправке сообщения пользователю {user_id}: {e}")
                        failed_count += 1
                
                result_text = (
                    f"✅ Оповещение отправлено!\n\n"
                    f"📦 Сессия: {session['session_name']}\n"
                    f"✅ Успешно отправлено: {sent_count} пользователям\n"
                )
                if failed_count > 0:
                    result_text += f"❌ Ошибок при отправке: {failed_count}\n"
                
                await update.message.reply_text(result_text)
                context.user_data.pop('notify_pending', None)
            else:
                context.user_data.pop('notify_pending', None)
                await update.message.reply_text("❌ У вас нет прав для отправки оповещений!")
    
    # Обработка оповещения активных заказов
    elif context.user_data.get('notify_active'):
        notify_data = context.user_data['notify_active']
        if notify_data.get('step') == 'waiting_message':
            if database.is_manager(user_id) or database.is_admin(user_id):
                session_id = notify_data['session_id']
                session = database.get_session(session_id)
                
                if not session:
                    context.user_data.pop('notify_active', None)
                    await update.message.reply_text("❌ Сессия не найдена!")
                    return
                
                message_text = update.message.text.strip()
                
                if not message_text:
                    await update.message.reply_text(
                        "❌ Текст сообщения не может быть пустым!\n\n"
                        "Введите текст сообщения:"
                    )
                    return
                
                # Получаем пользователей с активными заказами (pending или processing)
                user_ids = database.get_users_with_active_orders_by_session(session_id)
                
                if not user_ids:
                    await update.message.reply_text(
                        f"❌ В сессии '{session['session_name']}' нет пользователей с активными заказами!"
                    )
                    context.user_data.pop('notify_active', None)
                    return
                
                # Отправляем сообщения
                sent_count = 0
                failed_count = 0
                
                await update.message.reply_text(f"⏳ Отправка сообщений {len(user_ids)} пользователям...")
                
                for user_id in user_ids:
                    try:
                        await context.bot.send_message(
                            chat_id=user_id,
                            text=message_text
                        )
                        sent_count += 1
                    except Exception as e:
                        import logging
                        logging.getLogger(__name__).error(f"Ошибка при отправке сообщения пользователю {user_id}: {e}")
                        failed_count += 1
                
                result_text = (
                    f"✅ Оповещение отправлено!\n\n"
                    f"📦 Сессия: {session['session_name']}\n"
                    f"✅ Успешно отправлено: {sent_count} пользователям\n"
                )
                if failed_count > 0:
                    result_text += f"❌ Ошибок при отправке: {failed_count}\n"
                
                await update.message.reply_text(result_text)
                context.user_data.pop('notify_active', None)
            else:
                context.user_data.pop('notify_active', None)
                await update.message.reply_text("❌ У вас нет прав для отправки оповещений!")
    
    # Обработка изменения количества ящиков товара
    elif context.user_data.get('changing_box_volume'):
        if not database.is_admin(user_id):
            context.user_data.pop('changing_box_volume', None)
            await update.message.reply_text("❌ У вас нет прав для изменения количества ящиков!")
            return
        
        try:
            new_boxes_count = int(update.message.text.strip())
            if new_boxes_count >= 0:
                product_id = context.user_data['changing_box_volume']['product_id']
                old_boxes = context.user_data['changing_box_volume']['current_boxes']
                
                if database.update_product_boxes_count(product_id, new_boxes_count):
                    product = database.get_product(product_id)
                    await update.message.reply_text(
                        f"✅ Количество ящиков успешно изменено!\n\n"
                        f"Товар: {product['product_name']}\n"
                        f"Было: {old_boxes} ящиков\n"
                        f"Стало: {new_boxes_count} ящиков"
                    )
                    context.user_data.pop('changing_box_volume', None)
                else:
                    await update.message.reply_text("❌ Ошибка при изменении количества ящиков!")
            else:
                await update.message.reply_text("❌ Количество ящиков не может быть отрицательным!")
        except ValueError:
            await update.message.reply_text("❌ Введите корректное целое число!")
    
    # Обработка изменения заказа администратором
    elif context.user_data.get('waiting_for_order_to_edit'):
        if database.is_admin(user_id):
            order_number = update.message.text.strip()
            order = database.find_order_by_number(order_number)
            
            if order:
                order_items = database.get_order_items(order['order_id'])
                session = database.get_session(order['session_id'])
                
                items_text = "\n".join([
                    f"• {item['product_name']} x{item['quantity']} = {item['quantity'] * item['price']}₽"
                    for item in order_items
                ])
                
                from keyboards.order_edit import get_order_edit_keyboard
                keyboard = get_order_edit_keyboard(order['order_id'])
                
                await update.message.reply_text(
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
                context.user_data.pop('waiting_for_order_to_edit', None)
            else:
                await update.message.reply_text(
                    f"❌ Заказ с номером {order_number} не найден!\n\n"
                    f"Попробуйте еще раз."
                )
        else:
            context.user_data.pop('waiting_for_order_to_edit', None)
            await update.message.reply_text("❌ У вас нет прав для изменения заказов!")
    
    # Обработка редактирования количества товара в заказе
    elif context.user_data.get('editing_order_item'):
        if not database.is_admin(user_id):
            context.user_data.pop('editing_order_item', None)
            await update.message.reply_text("❌ У вас нет прав для редактирования заказов!")
            return
        
        try:
            new_quantity = int(update.message.text.strip())
            if new_quantity > 0:
                item_data = context.user_data['editing_order_item']
                order_id = item_data['order_id']
                item_id = item_data['item_id']
                
                if database.update_order_item_quantity(item_id, new_quantity):
                    order = database.get_order(order_id)
                    order_items = database.get_order_items(order_id)
                    
                    items_text = "\n".join([
                        f"• {item['product_name']} x{item['quantity']} = {item['quantity'] * item['price']}₽"
                        for item in order_items
                    ])
                    
                    from keyboards.order_edit_items import get_order_items_edit_keyboard
                    keyboard = get_order_items_edit_keyboard(order_id, order_items)
                    
                    await update.message.reply_text(
                        f"✅ Количество товара успешно изменено!\n\n"
                        f"Заказ #{order['order_number']}\n\n"
                        f"Текущий состав:\n{items_text}\n\n"
                        f"💰 Общая сумма: {order['total_amount']}₽",
                        reply_markup=keyboard
                    )
                    context.user_data.pop('editing_order_item', None)
                else:
                    await update.message.reply_text("❌ Ошибка при изменении количества товара!")
            else:
                await update.message.reply_text("❌ Количество должно быть больше нуля!")
        except ValueError:
            await update.message.reply_text("❌ Введите корректное целое число!")
    
    # Обработка добавления товара в заказ
    elif context.user_data.get('adding_item_to_order'):
        if not database.is_admin(user_id):
            context.user_data.pop('adding_item_to_order', None)
            await update.message.reply_text("❌ У вас нет прав для редактирования заказов!")
            return
        
        item_data = context.user_data['adding_item_to_order']
        step = item_data.get('step')
        text = update.message.text.strip()
        
        if step == 'quantity':
            try:
                quantity = int(text)
                if quantity > 0:
                    order_id = item_data['order_id']
                    product_id = item_data['product_id']
                    
                    if database.add_item_to_order(order_id, product_id, quantity):
                        order = database.get_order(order_id)
                        order_items = database.get_order_items(order_id)
                        
                        items_text = "\n".join([
                            f"• {item['product_name']} x{item['quantity']} = {item['quantity'] * item['price']}₽"
                            for item in order_items
                        ])
                        
                        from keyboards.order_edit_items import get_order_items_edit_keyboard
                        keyboard = get_order_items_edit_keyboard(order_id, order_items)
                        
                        await update.message.reply_text(
                            f"✅ Товар успешно добавлен в заказ!\n\n"
                            f"Заказ #{order['order_number']}\n\n"
                            f"Текущий состав:\n{items_text}\n\n"
                            f"💰 Общая сумма: {order['total_amount']}₽",
                            reply_markup=keyboard
                        )
                        context.user_data.pop('adding_item_to_order', None)
                    else:
                        await update.message.reply_text("❌ Ошибка при добавлении товара в заказ!")
                else:
                    await update.message.reply_text("❌ Количество должно быть больше нуля!")
            except ValueError:
                await update.message.reply_text("❌ Введите корректное целое число!")
    
    # Обработка добавления администратора
    elif context.user_data.get('waiting_for_admin_id'):
        if database.is_admin(user_id):
            try:
                admin_id = int(update.message.text.strip())
                
                # Проверяем, существует ли пользователь
                user_info = database.get_user_info(admin_id)
                if not user_info:
                    # Создаем минимальную запись пользователя
                    database.save_or_update_user(
                        type('User', (), {
                            'id': admin_id,
                            'username': None,
                            'first_name': f'User_{admin_id}',
                            'last_name': None,
                            'language_code': None,
                            'is_bot': False
                        })(),
                        admin_id
                    )
                
                if database.add_admin(admin_id):
                    context.user_data.pop('waiting_for_admin_id', None)
                    await update.message.reply_text(
                        f"✅ Администратор с ID {admin_id} успешно добавлен!"
                    )
                else:
                    await update.message.reply_text(
                        f"❌ Ошибка при добавлении администратора. Возможно, он уже является администратором."
                    )
            except ValueError:
                await update.message.reply_text("❌ Введите корректный ID пользователя (число)!")
        else:
            context.user_data.pop('waiting_for_admin_id', None)
            await update.message.reply_text("❌ У вас нет прав для добавления администраторов!")
    
    # Обработка добавления менеджера администратором
    elif context.user_data.get('waiting_for_manager_id'):
        if database.is_admin(user_id):
            try:
                manager_id = int(update.message.text.strip())
                
                # Проверяем, существует ли пользователь
                user_info = database.get_user_info(manager_id)
                if not user_info:
                    # Создаем минимальную запись пользователя
                    database.save_or_update_user(
                        type('User', (), {
                            'id': manager_id,
                            'username': None,
                            'first_name': f'User_{manager_id}',
                            'last_name': None,
                            'language_code': None,
                            'is_bot': False
                        })(),
                        manager_id
                    )
                
                if database.add_manager(manager_id):
                    context.user_data.pop('waiting_for_manager_id', None)
                    await update.message.reply_text(
                        f"✅ Менеджер с ID {manager_id} успешно добавлен!"
                    )
                else:
                    await update.message.reply_text(
                        f"❌ Ошибка при добавлении менеджера. Возможно, он уже является менеджером."
                    )
            except ValueError:
                await update.message.reply_text("❌ Введите корректный ID пользователя (число)!")
        else:
            context.user_data.pop('waiting_for_manager_id', None)
            await update.message.reply_text("❌ У вас нет прав для добавления менеджера!")
    
    else:
        # Обычное эхо-сообщение
        await update.message.reply_text(f"Вы написали: {update.message.text}")


async def handle_photo(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Обработчик фото для сканирования QR-кодов"""
    user_id = update.effective_user.id
    photo = update.message.photo[-1]  # Берем фото наибольшего размера
    
    try:
        # Скачиваем фото
        file = await context.bot.get_file(photo.file_id)
        photo_bytes = io.BytesIO()
        await file.download_to_memory(photo_bytes)
        photo_bytes.seek(0)
        
        # Декодируем QR-код
        from PIL import Image
        from pyzbar import pyzbar
        
        img = Image.open(photo_bytes)
        decoded_objects = pyzbar.decode(img)
        
        if decoded_objects:
            # Извлекаем номер заказа из QR-кода
            order_number = decoded_objects[0].data.decode('utf-8')
            order = database.find_order_by_number(order_number)
            
            if order:
                order_items = database.get_order_items(order['order_id'])
                session = database.get_session(order['session_id'])
                
                items_text = "\n".join([
                    f"• {item['product_name']} x{item['quantity']} = {item['quantity'] * item['price']}₽"
                    for item in order_items
                ])
                
                # Проверяем права пользователя
                is_admin_or_manager = database.is_admin(user_id) or database.is_manager(user_id)
                
                if is_admin_or_manager:
                    # Для админа и менеджера показываем полную информацию
                    await update.message.reply_text(
                        f"📋 Заказ #{order['order_number']}\n\n"
                        f"📦 Сессия: {session['session_name'] if session else 'Не найдена'}\n"
                        f"👤 ФИО: {order['full_name']}\n"
                        f"📱 Телефон: {order['phone_number']}\n"
                        f"📊 Статус: {database.get_order_status_ru(order['status'])}\n"
                        f"📅 Дата: {order['created_at']}\n\n"
                        f"Товары:\n{items_text}\n\n"
                        f"💰 Общая сумма: {order['total_amount']}₽"
                    )
                else:
                    # Для обычного пользователя показываем с маскировкой
                    import qr_code
                    masked_name = qr_code.mask_name(order['full_name'])
                    masked_phone = qr_code.mask_phone(order['phone_number'])
                    
                    # Проверяем, ожидает ли админ заказ для редактирования
                    if context.user_data.get('waiting_for_order_to_edit'):
                        from keyboards.order_edit import get_order_edit_keyboard
                        keyboard = get_order_edit_keyboard(order['order_id'])
                        await update.message.reply_text(
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
                        context.user_data.pop('waiting_for_order_to_edit', None)
                    else:
                        # Обычное сканирование для просмотра
                        masked_name = qr_code.mask_name(order['full_name'])
                        masked_phone = qr_code.mask_phone(order['phone_number'])
                        await update.message.reply_text(
                            f"📋 Заказ #{order['order_number']}\n\n"
                            f"📦 Сессия: {session['session_name'] if session else 'Не найдена'}\n"
                            f"👤 ФИО: {masked_name}\n"
                            f"📱 Телефон: {masked_phone}\n"
                            f"📊 Статус: {database.get_order_status_ru(order['status'])}\n\n"
                            f"Товары:\n{items_text}\n\n"
                            f"💰 Общая сумма: {order['total_amount']}₽"
                        )
            else:
                await update.message.reply_text(
                    f"❌ Заказ с номером {order_number} не найден!"
                )
        else:
            await update.message.reply_text(
                "❌ QR-код не распознан. Убедитесь, что фото четкое и QR-код хорошо виден."
            )
    except Exception as e:
        import logging
        logger = logging.getLogger(__name__)
        logger.error(f"Ошибка при обработке QR-кода: {e}")
        await update.message.reply_text(
            "❌ Ошибка при обработке QR-кода. Попробуйте еще раз."
        )
