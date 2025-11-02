from django.core.mail import send_mail
from django.conf import settings
from .models import EmailConfirmation


def send_confirmation_code(user, email):
    """Отправляет 6-значный код на email"""

    # Удаляем старые коды
    EmailConfirmation.objects.filter(user=user, confirmed_at__isnull=True).delete()

    # Создаем новый код
    confirmation = EmailConfirmation.objects.create(
        user=user,
        email=email,
    )

    # Текст письма с кодом
    subject = 'Код подтверждения email'
    message = f"""
    Здравствуйте, {user.username}!

    Ваш код подтверждения: {confirmation.code}

    Введите этот код в поле подтверждения в вашем профиле.

    Код действителен 15 минут.
    
    С уважением, Администратор сайта :)
    """

    # Отправляем письмо
    send_mail(
        subject,
        message,
        settings.EMAIL_HOST_USER,
        [email],
        fail_silently=False,
    )

    return confirmation.code


def send_recovery_code(user, email):
    """Отправляет код для восстановления пароля"""
    # Удаляем старые коды восстановления
    EmailConfirmation.objects.filter(
        user=user,
        email=email,
        confirmed_at__isnull=True
    ).delete()

    # Создаем новый код восстановления
    recovery = EmailConfirmation.objects.create(
        user=user,
        email=email,
    )

    subject = 'Код восстановления пароля'
    message = f"""
Здравствуйте, {user.username}!

Ваш код для восстановления пароля: {recovery.code}

Введите этот код в форме восстановления пароля.

Код действителен 15 минут.

Если вы не запрашивали восстановление пароля, проигнорируйте это письмо.

С уважением,
Система бронирования переговорок
"""

    send_mail(
        subject,
        message,
        settings.EMAIL_HOST_USER,
        [email],
        fail_silently=False,
    )

    return recovery.code