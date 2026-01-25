import database
import sys
import io

# Настройка кодировки для Windows
if sys.platform == 'win32':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

database.init_database()

session = database.get_session(9)
if session:
    print(f"Сессия: {session['session_name']}")
    print(f"Активна: {database.is_session_trading_active(9)}")
    
    products = database.get_products_by_session(9)
    print(f"\nТоваров: {len(products)}")
    for p in products:
        print(f"  - {p['product_name']}: {p['price']}₽ ({p['boxes_count']} ящиков)")
    
    orders = database.get_session_orders(9)
    print(f"\nЗаказов: {len(orders)}")
    for o in orders:
        print(f"  - Заказ #{o['order_number']}: {o['full_name']} - {database.get_order_status_ru(o['status'])} - {o['total_amount']}₽")
else:
    print("Сессия не найдена!")
