import qrcode
import io
from PIL import Image


def generate_qr_code(order_number: str) -> io.BytesIO:
    """Генерирует QR-код с номером заказа"""
    qr = qrcode.QRCode(
        version=1,
        error_correction=qrcode.constants.ERROR_CORRECT_L,
        box_size=10,
        border=4,
    )
    qr.add_data(order_number)
    qr.make(fit=True)
    
    img = qr.make_image(fill_color="black", back_color="white")
    
    # Сохраняем в байты
    qr_bytes = io.BytesIO()
    img.save(qr_bytes, format='PNG')
    qr_bytes.seek(0)
    
    return qr_bytes


def mask_phone(phone: str) -> str:
    """Маскирует номер телефона звездочками"""
    if not phone or len(phone) < 4:
        return phone
    return phone[:2] + "*" * (len(phone) - 4) + phone[-2:]


def mask_name(name: str) -> str:
    """Маскирует ФИО звездочками"""
    if not name:
        return name
    parts = name.split()
    if len(parts) == 1:
        # Только имя
        if len(parts[0]) <= 2:
            return parts[0][0] + "*"
        return parts[0][0] + "*" * (len(parts[0]) - 2) + parts[0][-1]
    elif len(parts) == 2:
        # Имя и фамилия
        return parts[0][0] + "*" * (len(parts[0]) - 1) + " " + parts[1][0] + "*" * (len(parts[1]) - 1)
    else:
        # ФИО
        return parts[0][0] + "*" * (len(parts[0]) - 1) + " " + parts[1][0] + "*" * (len(parts[1]) - 1) + " " + parts[2][0] + "*" * (len(parts[2]) - 1)


def mask_phone_channel(phone: str) -> str:
    """Маскирует номер телефона для канала: показывает первую цифру и последние 4, остальное убирает"""
    if not phone or len(phone) < 5:
        return phone
    return phone[0] + phone[-4:]


def mask_name_channel(name: str) -> str:
    """Маскирует ФИО для канала: показывает только имя, остальное убирает"""
    if not name:
        return name
    parts = name.split()
    if len(parts) == 0:
        return name
    # Возвращаем только первое слово (имя)
    return parts[0]
