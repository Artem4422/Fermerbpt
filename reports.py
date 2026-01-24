import sqlite3
import database
from openpyxl import Workbook
from openpyxl.styles import Font, Alignment, PatternFill, Border, Side
from openpyxl.utils import get_column_letter
from datetime import datetime
import io


def generate_session_report_excel(session_id: int) -> io.BytesIO:
    """Генерирует полный Excel отчет по сессии"""
    session = database.get_session(session_id)
    if not session:
        raise ValueError("Сессия не найдена")
    
    # Получаем данные
    orders = database.get_session_orders(session_id)
    products = database.get_products_by_session(session_id)
    
    # Создаем рабочую книгу
    wb = Workbook()
    
    # Удаляем дефолтный лист
    wb.remove(wb.active)
    
    # Стили
    header_fill = PatternFill(start_color="366092", end_color="366092", fill_type="solid")
    header_font = Font(bold=True, color="FFFFFF", size=12)
    title_font = Font(bold=True, size=14)
    border = Border(
        left=Side(style='thin'),
        right=Side(style='thin'),
        top=Side(style='thin'),
        bottom=Side(style='thin')
    )
    center_align = Alignment(horizontal='center', vertical='center')
    
    # Лист 1: Общая информация
    ws_summary = wb.create_sheet("Общая информация")
    
    ws_summary['A1'] = f"ОТЧЕТ ПО СЕССИИ: {session['session_name']}"
    ws_summary['A1'].font = title_font
    ws_summary.merge_cells('A1:D1')
    
    ws_summary['A3'] = "Дата создания сессии:"
    ws_summary['B3'] = session['created_at']
    ws_summary['A4'] = "Всего заказов:"
    ws_summary['B4'] = len(orders)
    
    completed_orders = [o for o in orders if o['status'] == 'completed']
    pending_orders = [o for o in orders if o['status'] == 'pending']
    processing_orders = [o for o in orders if o['status'] == 'processing']
    cancelled_orders = [o for o in orders if o['status'] == 'cancelled']
    
    ws_summary['A5'] = "Выдано заказов:"
    ws_summary['B5'] = len(completed_orders)
    ws_summary['A6'] = "Ожидает обработки:"
    ws_summary['B6'] = len(pending_orders)
    ws_summary['A7'] = "В обработке:"
    ws_summary['B7'] = len(processing_orders)
    ws_summary['A8'] = "Отменено:"
    ws_summary['B8'] = len(cancelled_orders)
    
    total_revenue = sum(o['total_amount'] for o in completed_orders)
    ws_summary['A9'] = "Выручка (выданные заказы):"
    ws_summary['B9'] = total_revenue
    ws_summary['B9'].number_format = '#,##0.00₽'
    
    # Лист 2: Продажи
    ws_sales = wb.create_sheet("Продажи")
    
    headers_sales = ["№ заказа", "ФИО", "Телефон", "Товары", "Количество ящиков", "Сумма", "Статус", "Дата"]
    for col, header in enumerate(headers_sales, 1):
        cell = ws_sales.cell(row=1, column=col)
        cell.value = header
        cell.font = header_font
        cell.fill = header_fill
        cell.alignment = center_align
        cell.border = border
    
    row = 2
    total_boxes_sold = 0
    for order in orders:
        order_items = database.get_order_items(order['order_id'])
        boxes_in_order = sum(item['quantity'] for item in order_items)
        total_boxes_sold += boxes_in_order if order['status'] == 'completed' else 0
        
        items_text = ", ".join([f"{item['product_name']} x{item['quantity']}" for item in order_items])
        
        ws_sales.cell(row=row, column=1).value = order['order_number']
        ws_sales.cell(row=row, column=2).value = order['full_name']
        ws_sales.cell(row=row, column=3).value = order['phone_number']
        ws_sales.cell(row=row, column=4).value = items_text
        ws_sales.cell(row=row, column=5).value = boxes_in_order
        ws_sales.cell(row=row, column=6).value = order['total_amount']
        ws_sales.cell(row=row, column=6).number_format = '#,##0.00₽'
        ws_sales.cell(row=row, column=7).value = database.get_order_status_ru(order['status'])
        ws_sales.cell(row=row, column=8).value = order['created_at']
        
        for col in range(1, 9):
            ws_sales.cell(row=row, column=col).border = border
        
        row += 1
    
    # Автоподбор ширины колонок
    for col in range(1, 9):
        ws_sales.column_dimensions[get_column_letter(col)].width = 15
    
    # Лист 3: Товары и остатки
    ws_products = wb.create_sheet("Товары и остатки")
    
    headers_products = ["Товар", "Цена за ящик", "Начальное количество", "Продано", "Остаток", "Выручка"]
    for col, header in enumerate(headers_products, 1):
        cell = ws_products.cell(row=1, column=col)
        cell.value = header
        cell.font = header_font
        cell.fill = header_fill
        cell.alignment = center_align
        cell.border = border
    
    row = 2
    for product in products:
        # Подсчитываем проданное количество
        sold_count = 0
        product_revenue = 0
        
        for order in completed_orders:
            order_items = database.get_order_items(order['order_id'])
            for item in order_items:
                if item['product_id'] == product['product_id']:
                    sold_count += item['quantity']
                    product_revenue += item['quantity'] * item['price']
        
        remaining = product['boxes_count']
        
        ws_products.cell(row=row, column=1).value = product['product_name']
        ws_products.cell(row=row, column=2).value = product['price']
        ws_products.cell(row=row, column=2).number_format = '#,##0.00₽'
        ws_products.cell(row=row, column=3).value = product['boxes_count'] + sold_count  # Начальное = текущее + проданное
        ws_products.cell(row=row, column=4).value = sold_count
        ws_products.cell(row=row, column=5).value = remaining
        ws_products.cell(row=row, column=6).value = product_revenue
        ws_products.cell(row=row, column=6).number_format = '#,##0.00₽'
        
        for col in range(1, 7):
            ws_products.cell(row=row, column=col).border = border
        
        row += 1
    
    # Автоподбор ширины колонок
    for col in range(1, 7):
        ws_products.column_dimensions[get_column_letter(col)].width = 20
    
    # Лист 4: Клиенты (отсортированные по количеству заказов)
    ws_customers = wb.create_sheet("Клиенты")
    
    headers_customers = ["№", "ФИО", "Телефон", "Количество заказов", "Номера заказов", "Общая сумма", "Всего ящиков"]
    for col, header in enumerate(headers_customers, 1):
        cell = ws_customers.cell(row=1, column=col)
        cell.value = header
        cell.font = header_font
        cell.fill = header_fill
        cell.alignment = center_align
        cell.border = border
    
    # Группируем заказы по клиентам
    customers_dict = {}
    for order in orders:
        # Используем комбинацию ФИО и телефона как ключ
        customer_key = f"{order['full_name']}_{order['phone_number']}"
        
        if customer_key not in customers_dict:
            customers_dict[customer_key] = {
                'full_name': order['full_name'],
                'phone_number': order['phone_number'],
                'user_id': order['user_id'],
                'orders': [],
                'total_amount': 0,
                'total_boxes': 0
            }
        
        customers_dict[customer_key]['orders'].append(order)
        customers_dict[customer_key]['total_amount'] += order['total_amount']
        
        # Подсчитываем ящики в заказе
        order_items = database.get_order_items(order['order_id'])
        boxes_in_order = sum(item['quantity'] for item in order_items)
        customers_dict[customer_key]['total_boxes'] += boxes_in_order
    
    # Сортируем клиентов по количеству заказов (от большего к меньшему)
    customers_list = sorted(
        customers_dict.values(),
        key=lambda x: len(x['orders']),
        reverse=True
    )
    
    row = 2
    for idx, customer in enumerate(customers_list, 1):
        order_numbers = ", ".join([f"#{o['order_number']}" for o in customer['orders']])
        
        ws_customers.cell(row=row, column=1).value = idx
        ws_customers.cell(row=row, column=2).value = customer['full_name']
        ws_customers.cell(row=row, column=3).value = customer['phone_number']
        ws_customers.cell(row=row, column=4).value = len(customer['orders'])
        ws_customers.cell(row=row, column=5).value = order_numbers
        ws_customers.cell(row=row, column=6).value = customer['total_amount']
        ws_customers.cell(row=row, column=6).number_format = '#,##0.00₽'
        ws_customers.cell(row=row, column=7).value = customer['total_boxes']
        
        for col in range(1, 8):
            ws_customers.cell(row=row, column=col).border = border
        
        row += 1
    
    # Автоподбор ширины колонок
    ws_customers.column_dimensions['A'].width = 8
    ws_customers.column_dimensions['B'].width = 25
    ws_customers.column_dimensions['C'].width = 15
    ws_customers.column_dimensions['D'].width = 18
    ws_customers.column_dimensions['E'].width = 50
    ws_customers.column_dimensions['F'].width = 15
    ws_customers.column_dimensions['G'].width = 15
    
    # Лист 5: Статистика
    ws_stats = wb.create_sheet("Статистика")
    
    ws_stats['A1'] = "СТАТИСТИКА ПО СЕССИИ"
    ws_stats['A1'].font = title_font
    ws_stats.merge_cells('A1:B1')
    
    row = 3
    stats = [
        ("Всего заказов", len(orders)),
        ("Выдано заказов", len(completed_orders)),
        ("Ожидает обработки", len(pending_orders)),
        ("В обработке", len(processing_orders)),
        ("Отменено", len(cancelled_orders)),
        ("", ""),
        ("Всего клиентов", len(customers_list)),
        ("", ""),
        ("Общая выручка", total_revenue),
        ("Всего продано ящиков", total_boxes_sold),
        ("Средний чек", total_revenue / len(completed_orders) if completed_orders else 0),
    ]
    
    for label, value in stats:
        ws_stats.cell(row=row, column=1).value = label
        ws_stats.cell(row=row, column=1).font = Font(bold=True)
        if isinstance(value, (int, float)) and value != 0:
            ws_stats.cell(row=row, column=2).value = value
            if 'выручка' in label.lower() or 'чек' in label.lower():
                ws_stats.cell(row=row, column=2).number_format = '#,##0.00₽'
        else:
            ws_stats.cell(row=row, column=2).value = value
        row += 1
    
    # Сохраняем в байты
    excel_bytes = io.BytesIO()
    wb.save(excel_bytes)
    excel_bytes.seek(0)
    
    return excel_bytes


def generate_period_report_excel(period: str) -> io.BytesIO:
    """Генерирует полный Excel отчет за период по всем сессиям"""
    from datetime import datetime, timedelta
    
    # Получаем данные за период
    orders = database.get_orders_by_period(period)
    
    # Получаем все сессии, которые были в этом периоде
    session_ids = list(set([o['session_id'] for o in orders]))
    sessions = [database.get_session(sid) for sid in session_ids if database.get_session(sid)]
    
    # Определяем название периода
    period_names = {
        "week": "неделю",
        "month": "месяц",
        "year": "год",
        "all_time": "все время"
    }
    period_name = period_names.get(period, period)
    
    # Создаем рабочую книгу
    wb = Workbook()
    wb.remove(wb.active)
    
    # Стили
    header_fill = PatternFill(start_color="366092", end_color="366092", fill_type="solid")
    header_font = Font(bold=True, color="FFFFFF", size=12)
    title_font = Font(bold=True, size=14)
    border = Border(
        left=Side(style='thin'),
        right=Side(style='thin'),
        top=Side(style='thin'),
        bottom=Side(style='thin')
    )
    center_align = Alignment(horizontal='center', vertical='center')
    
    # Лист 1: Общая информация
    ws_summary = wb.create_sheet("Общая информация")
    
    ws_summary['A1'] = f"ОТЧЕТ ЗА {period_name.upper()}"
    ws_summary['A1'].font = title_font
    ws_summary.merge_cells('A1:D1')
    
    completed_orders = [o for o in orders if o['status'] == 'completed']
    pending_orders = [o for o in orders if o['status'] == 'pending']
    processing_orders = [o for o in orders if o['status'] == 'processing']
    cancelled_orders = [o for o in orders if o['status'] == 'cancelled']
    
    total_revenue = sum(o['total_amount'] for o in completed_orders)
    total_boxes_sold = 0
    for order in completed_orders:
        order_items = database.get_order_items(order['order_id'])
        total_boxes_sold += sum(item['quantity'] for item in order_items)
    
    ws_summary['A3'] = "Период:"
    ws_summary['B3'] = period_name
    ws_summary['A4'] = "Всего заказов:"
    ws_summary['B4'] = len(orders)
    ws_summary['A5'] = "Выдано заказов:"
    ws_summary['B5'] = len(completed_orders)
    ws_summary['A6'] = "Ожидает обработки:"
    ws_summary['B6'] = len(pending_orders)
    ws_summary['A7'] = "В обработке:"
    ws_summary['B7'] = len(processing_orders)
    ws_summary['A8'] = "Отменено:"
    ws_summary['B8'] = len(cancelled_orders)
    ws_summary['A9'] = "Всего сессий:"
    ws_summary['B9'] = len(sessions)
    ws_summary['A10'] = "Общая выручка:"
    ws_summary['B10'] = total_revenue
    ws_summary['B10'].number_format = '#,##0.00₽'
    ws_summary['A11'] = "Всего продано ящиков:"
    ws_summary['B11'] = total_boxes_sold
    
    # Лист 2: Все заказы
    ws_orders = wb.create_sheet("Все заказы")
    
    headers_orders = ["№ заказа", "Сессия", "ФИО", "Телефон", "Товары", "Ящиков", "Сумма", "Статус", "Дата"]
    for col, header in enumerate(headers_orders, 1):
        cell = ws_orders.cell(row=1, column=col)
        cell.value = header
        cell.font = header_font
        cell.fill = header_fill
        cell.alignment = center_align
        cell.border = border
    
    row = 2
    for order in orders:
        session = database.get_session(order['session_id'])
        session_name = session['session_name'] if session else f"Сессия {order['session_id']}"
        order_items = database.get_order_items(order['order_id'])
        boxes_in_order = sum(item['quantity'] for item in order_items)
        
        ws_orders.cell(row=row, column=1).value = order['order_number']
        ws_orders.cell(row=row, column=2).value = session_name
        ws_orders.cell(row=row, column=3).value = order['full_name']
        ws_orders.cell(row=row, column=4).value = order['phone_number']
        ws_orders.cell(row=row, column=5).value = order['items']
        ws_orders.cell(row=row, column=6).value = boxes_in_order
        ws_orders.cell(row=row, column=7).value = order['total_amount']
        ws_orders.cell(row=row, column=7).number_format = '#,##0.00₽'
        ws_orders.cell(row=row, column=8).value = database.get_order_status_ru(order['status'])
        ws_orders.cell(row=row, column=9).value = order['created_at']
        
        for col in range(1, 10):
            ws_orders.cell(row=row, column=col).border = border
        
        row += 1
    
    # Автоподбор ширины колонок
    for col in range(1, 10):
        ws_orders.column_dimensions[get_column_letter(col)].width = 15
    
    # Лист 3: Клиенты (отсортированные по количеству заказов)
    ws_customers = wb.create_sheet("Клиенты")
    
    headers_customers = ["№", "ФИО", "Телефон", "Количество заказов", "Номера заказов", "Общая сумма", "Всего ящиков"]
    for col, header in enumerate(headers_customers, 1):
        cell = ws_customers.cell(row=1, column=col)
        cell.value = header
        cell.font = header_font
        cell.fill = header_fill
        cell.alignment = center_align
        cell.border = border
    
    # Группируем заказы по клиентам
    customers_dict = {}
    for order in orders:
        customer_key = f"{order['full_name']}_{order['phone_number']}"
        
        if customer_key not in customers_dict:
            customers_dict[customer_key] = {
                'full_name': order['full_name'],
                'phone_number': order['phone_number'],
                'orders': [],
                'total_amount': 0,
                'total_boxes': 0
            }
        
        customers_dict[customer_key]['orders'].append(order)
        customers_dict[customer_key]['total_amount'] += order['total_amount']
        
        order_items = database.get_order_items(order['order_id'])
        boxes_in_order = sum(item['quantity'] for item in order_items)
        customers_dict[customer_key]['total_boxes'] += boxes_in_order
    
    # Сортируем клиентов по количеству заказов
    customers_list = sorted(
        customers_dict.values(),
        key=lambda x: len(x['orders']),
        reverse=True
    )
    
    row = 2
    for idx, customer in enumerate(customers_list, 1):
        order_numbers = ", ".join([f"#{o['order_number']}" for o in customer['orders']])
        
        ws_customers.cell(row=row, column=1).value = idx
        ws_customers.cell(row=row, column=2).value = customer['full_name']
        ws_customers.cell(row=row, column=3).value = customer['phone_number']
        ws_customers.cell(row=row, column=4).value = len(customer['orders'])
        ws_customers.cell(row=row, column=5).value = order_numbers
        ws_customers.cell(row=row, column=6).value = customer['total_amount']
        ws_customers.cell(row=row, column=6).number_format = '#,##0.00₽'
        ws_customers.cell(row=row, column=7).value = customer['total_boxes']
        
        for col in range(1, 8):
            ws_customers.cell(row=row, column=col).border = border
        
        row += 1
    
    # Автоподбор ширины колонок
    ws_customers.column_dimensions['A'].width = 8
    ws_customers.column_dimensions['B'].width = 25
    ws_customers.column_dimensions['C'].width = 15
    ws_customers.column_dimensions['D'].width = 18
    ws_customers.column_dimensions['E'].width = 50
    ws_customers.column_dimensions['F'].width = 15
    ws_customers.column_dimensions['G'].width = 15
    
    # Лист 4: Статистика по сессиям
    ws_sessions = wb.create_sheet("Статистика по сессиям")
    
    headers_sessions = ["Сессия", "Заказов", "Выдано", "Выручка", "Ящиков продано"]
    for col, header in enumerate(headers_sessions, 1):
        cell = ws_sessions.cell(row=1, column=col)
        cell.value = header
        cell.font = header_font
        cell.fill = header_fill
        cell.alignment = center_align
        cell.border = border
    
    row = 2
    for session in sessions:
        session_orders = [o for o in orders if o['session_id'] == session['session_id']]
        session_completed = [o for o in session_orders if o['status'] == 'completed']
        session_revenue = sum(o['total_amount'] for o in session_completed)
        session_boxes = 0
        for order in session_completed:
            order_items = database.get_order_items(order['order_id'])
            session_boxes += sum(item['quantity'] for item in order_items)
        
        ws_sessions.cell(row=row, column=1).value = session['session_name']
        ws_sessions.cell(row=row, column=2).value = len(session_orders)
        ws_sessions.cell(row=row, column=3).value = len(session_completed)
        ws_sessions.cell(row=row, column=4).value = session_revenue
        ws_sessions.cell(row=row, column=4).number_format = '#,##0.00₽'
        ws_sessions.cell(row=row, column=5).value = session_boxes
        
        for col in range(1, 6):
            ws_sessions.cell(row=row, column=col).border = border
        
        row += 1
    
    # Автоподбор ширины колонок
    for col in range(1, 6):
        ws_sessions.column_dimensions[get_column_letter(col)].width = 20
    
    # Сохраняем в байты
    excel_bytes = io.BytesIO()
    wb.save(excel_bytes)
    excel_bytes.seek(0)
    
    return excel_bytes
