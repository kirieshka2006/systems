from django.core.mail import send_mail
from django.utils.timezone import localtime
from django.conf import settings

def send_booking_confirmation(booking):
    user = booking.user
    room = booking.room

    start = localtime(booking.start_time)
    end = localtime(booking.end_time)

    subject = f"Ваше бронирование подтверждено — {room.name}"

    message = f"""
Здравствуйте, {user.first_name or user.username}!

Ваше бронирование подтверждено.

📅 Дата: {start.strftime('%d.%m.%Y')}
⏰ Время: {start.strftime('%H:%M')} — {end.strftime('%H:%M')}
⏱ Длительность: {(booking.end_time - booking.start_time).seconds // 3600} часа
🏢 Местоположение: Скоро будет указано
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
