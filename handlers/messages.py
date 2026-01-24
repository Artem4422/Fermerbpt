from telegram import Update
from telegram.ext import ContextTypes
import database


async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Обработчик текстовых сообщений"""
    user_id = update.effective_user.id
    
    # Проверяем, ожидаем ли мы имя сессии от администратора
    if context.user_data.get('waiting_for_session_name'):
        if database.is_admin(user_id):
            session_name = update.message.text.strip()
            
            if len(session_name) > 0:
                session_id = database.add_session(session_name, user_id)
                if session_id:
                    context.user_data['waiting_for_session_name'] = False
                    await update.message.reply_text(
                        f"✅ Сессия '{session_name}' успешно создана!"
                    )
                else:
                    await update.message.reply_text(
                        "❌ Ошибка при создании сессии. Возможно, сессия с таким именем уже существует."
                    )
            else:
                await update.message.reply_text("❌ Имя сессии не может быть пустым!")
        else:
            context.user_data['waiting_for_session_name'] = False
            await update.message.reply_text("❌ У вас нет прав для создания сессии!")
    
    # Обработка добавления товара
    elif context.user_data.get('adding_product'):
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
                    
                    await update.message.reply_text(
                        f"✅ Заказ успешно создан!\n\n"
                        f"📋 Номер заказа: #{order['order_number']}\n"
                        f"📦 Сессия: {session['session_name']}\n"
                        f"👤 ФИО: {order['full_name']}\n"
                        f"📱 Телефон: {order['phone_number']}\n\n"
                        f"Товары:\n{items_text}\n\n"
                        f"💰 Общая сумма: {order['total_amount']}₽{continue_text}",
                        reply_markup=back_keyboard if back_keyboard else products_keyboard
                    )
                    
                    # Очищаем данные покупки
                    context.user_data.pop('purchase', None)
                else:
                    await update.message.reply_text("❌ Ошибка при создании заказа!")
            else:
                await update.message.reply_text("❌ ФИО не может быть пустым!")
    
    # Обработка поиска заказа менеджером
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
                context.user_data.pop('waiting_for_order_number', None)
            else:
                await update.message.reply_text(
                    f"❌ Заказ с номером {order_number} не найден!\n\n"
                    f"Попробуйте еще раз или вернитесь в панель менеджера."
                )
        else:
            context.user_data.pop('waiting_for_order_number', None)
            await update.message.reply_text("❌ У вас нет прав для поиска заказов!")
    
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
