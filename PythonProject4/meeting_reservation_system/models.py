from django.contrib.auth.models import AbstractUser
from django.db import models
import random
from django.utils import timezone
from datetime import timedelta
from django.core.validators import MinValueValidator, MaxValueValidator


class FAQ(models.Model):
    CATEGORY_CHOICES = [
        ('general', '📋 Общие вопросы'),
        ('booking', '📅 Бронирование'),
        ('payment', '💳 Оплата'),
        ('technical', '🛠️ Технические вопросы'),
    ]

    question = models.CharField(max_length=200, verbose_name="Вопрос")
    answer = models.TextField(verbose_name="Ответ")
    category = models.CharField(max_length=20, choices=CATEGORY_CHOICES, default='general')
    order = models.IntegerField(default=0, verbose_name="Порядок отображения")
    is_active = models.BooleanField(default=True, verbose_name="Активно")

    class Meta:
        ordering = ['order', 'id']

    def __str__(self):
        return self.question

class User(AbstractUser):
    ROLE_CHOICES = [
        ('admin', 'Администратор'),
        ('manager', 'Менеджер'),
        ('user', 'Пользователь'),
    ]

    GENDER_CHOICES = [
        ('M', 'Мужской'),
        ('F', 'Женский'),
    ]

    role = models.CharField(max_length=10, choices=ROLE_CHOICES, default='user')
    phone = models.CharField(max_length=15, blank=True)
    avatar = models.ImageField(upload_to='avatars/', blank=True, null=True)
    email_verification_code = models.CharField(max_length=6, blank=True, null=True)
    email_verified = models.BooleanField(default=False)

    # ★★★ НОВЫЕ ПОЛЯ ★★★
    first_name = models.CharField(max_length=30, blank=True)  # Имя
    last_name = models.CharField(max_length=30, blank=True)  # Фамилия
    patronymic = models.CharField(max_length=30, blank=True)  # Отчество
    birth_date = models.DateField(null=True, blank=True)  # Дата рождения
    gender = models.CharField(max_length=1, choices=GENDER_CHOICES, blank=True)  # Пол

    # Добавляем related_name чтобы избежать конфликтов
    groups = models.ManyToManyField(
        'auth.Group',
        verbose_name='groups',
        blank=True,
        help_text='The groups this user belongs to.',
        related_name='custom_user_set',  # ← ИЗМЕНИЛ
        related_query_name='user',
    )
    user_permissions = models.ManyToManyField(
        'auth.Permission',
        verbose_name='user permissions',
        blank=True,
        help_text='Specific permissions for this user.',
        related_name='custom_user_set',  # ← ИЗМЕНИЛ
        related_query_name='user',
    )


class SupportTicket(models.Model):
    STATUS_CHOICES = [
        ('open', '🔴 Открыт'),
        ('in_progress', '🟡 В работе'),
        ('closed', '🟢 Закрыт'),
    ]

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='tickets')
    subject = models.CharField(max_length=200, verbose_name="Тема вопроса")
    message = models.TextField(verbose_name="Сообщение")
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='open')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    last_activity = models.DateTimeField(auto_now=True)  # Дата последней активности
    auto_close_date = models.DateTimeField(null=True, blank=True)  # Дата авто-закрытия

    def __str__(self):
        return f"{self.user.username} - {self.subject}"


class TicketResponse(models.Model):
    ticket = models.ForeignKey(SupportTicket, on_delete=models.CASCADE, related_name='responses')
    user = models.ForeignKey(User, on_delete=models.CASCADE, verbose_name="Ответивший")
    message = models.TextField(verbose_name="Ответ")
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Ответ на {self.ticket.subject}"


class Room(models.Model):
    CATEGORY_CHOICES = [
        ('economy', '🟢 Эконом'),
        ('standard', '🔵 Стандарт'),
        ('comfort', '🟡 Комфорт'),
        ('vip', '🟣 VIP'),
        ('luxury', '🔴 Люкс'),
    ]

    STATUS_CHOICES = [
        ('active', '✅ Активна'),
        ('maintenance', '🚧 На ремонте'),
        ('hidden', '🔒 Скрыта'),
        ('inactive', '❌ Неактивна'),
    ]

    category = models.CharField(max_length=20, choices=CATEGORY_CHOICES, default='standard')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='active')
    name = models.CharField(max_length=100)
    location = models.CharField(max_length=200)
    capacity = models.IntegerField()
    equipment = models.TextField(
        blank=True,
        help_text="Вводите каждый пункт оборудования с новой строки. Например:\n- Проектор\n- Маркерная доска\n- Wi-Fi\n- Кондиционер"
    )
    price_per_hour = models.DecimalField(max_digits=10, decimal_places=2)
    image = models.ImageField(upload_to='rooms/', blank=True, null=True)
    is_active = models.BooleanField(default=True)
    amenities = models.JSONField(default=list, blank=True)

    def __str__(self):
        return self.name

    @property
    def equipment_list(self):
        """Возвращает список оборудования"""
        if self.equipment:
            return [item.strip() for item in self.equipment.split('\n') if item.strip()]
        return []

    def get_equipment_columns(self):
        """Разделяет оборудование на две колонки"""
        items = self.equipment_list
        if not items:
            return [], []

        mid = (len(items) + 1) // 2  # Делим пополам
        return items[:mid], items[mid:]


class EmailConfirmation(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='email_confirmations')
    email = models.EmailField()
    code = models.CharField(max_length=6)  # 6-значный код
    created_at = models.DateTimeField(auto_now_add=True)
    confirmed_at = models.DateTimeField(null=True, blank=True)

    def is_expired(self):
        """Проверяет, не устарел ли код (15 минут)"""
        expiration_date = self.created_at + timedelta(minutes=15)
        return timezone.now() > expiration_date

    def generate_code(self):
        """Создает 6-значный код"""
        return str(random.randint(100000, 999999))

    def save(self, *args, **kwargs):
        if not self.code:
            self.code = self.generate_code()
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.user.username} - {self.email} - {self.code}"


class Booking(models.Model):
    STATUS_CHOICES = [
        ('pending', '⏳ Ожидание'),
        ('confirmed', '✅ Подтверждено'),
        ('cancelled', '❌ Отменено'),
        ('completed', '🔵 Завершено'),
    ]
    # ★★★ ДОБАВЬ ЭТО ПОЛЕ ДЛЯ ХРАНЕНИЯ ИЗМЕНЕННОЙ ЦЕНЫ ★★★
    custom_price = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        null=True,
        blank=True,
        verbose_name="Измененная цена менеджером"
    )

    @property
    def duration_hours(self):
        """Возвращает продолжительность в часах"""
        if self.start_time and self.end_time:
            duration = self.end_time - self.start_time
            return int(duration.total_seconds() // 3600)
        return 0

    @property
    def total_price(self):
        """Возвращает общую стоимость"""
        if self.custom_price:
            return self.custom_price
        if hasattr(self, 'room') and self.room:
            return self.duration_hours * self.room.price_per_hour
        return 0

    user = models.ForeignKey(User, on_delete=models.CASCADE)
    room = models.ForeignKey(Room, on_delete=models.CASCADE)
    start_time = models.DateTimeField()
    end_time = models.DateTimeField()
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='pending')
    created_at = models.DateTimeField(auto_now_add=True)
    participants_count = models.IntegerField(default=1)  # ★★★ кол-во участников
    description = models.TextField(blank=True)  # ★★★ описание встречи
    manager_comment = models.TextField(blank=True, null=True)

    def __str__(self):
        return f"{self.user.username} - {self.room.name} - {self.start_time.strftime('%d.%m.%Y %H:%M')}"