from django.core.mail import send_mail
from django.utils.timezone import localtime
from django.conf import settings

def send_booking_confirmation(booking):
    user = booking.user
    room = booking.room

    start = localtime(booking.start_time)
    end = localtime(booking.end_time)

    subject = f"Ваше бронирование подтверждено — {room.name}"

    # 🏢 ОФИС
    office = room.office

    if office:
        office_info = f"""
🏢 Месторасположение:
Название офиса: {office.name}
Адрес: {office.address}
Телефон: {office.phone or "не указан"}
Часы работы: {office.work_hours or "не указаны"}
Ссылка на карту: {office.yandex_map_url or "не указана"}
"""
    else:
        office_info = "🏢 Месторасположение: офис не выбран\n"

    # 📩 ОСНОВНОЕ ПИСЬМО
    message = f"""
Здравствуйте, {user.first_name or user.username}!

Ваше бронирование подтверждено.

📅 Дата: {start.strftime('%d.%m.%Y')}
⏰ Время: {start.strftime('%H:%M')} — {end.strftime('%H:%M')}
⏱ Длительность: {(booking.end_time - booking.start_time).seconds // 3600} часа

{office_info}

💰 Итоговая стоимость: {booking.total_price} руб.
"""

    if booking.description:
        message += f"💬 Ваши пожелания:\n{booking.description}\n\n"

    if booking.manager_comment:
        message += f"📝 Комментарий менеджера:\n{booking.manager_comment}\n\n"

    message += "Если у вас возникнут вопросы — просто ответьте на это письмо."

    send_mail(
        subject,
        message,
        settings.EMAIL_HOST_USER,
        [user.email],
        fail_silently=False,
    )
