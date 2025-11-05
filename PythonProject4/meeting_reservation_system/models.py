from django.contrib.auth.models import AbstractUser
from django.db import models
import random
from django.utils import timezone
from datetime import timedelta
from django.core.validators import MinValueValidator, MaxValueValidator

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
    first_name = models.CharField(max_length=30, blank=True)      # Имя
    last_name = models.CharField(max_length=30, blank=True)       # Фамилия
    patronymic = models.CharField(max_length=30, blank=True)      # Отчество
    birth_date = models.DateField(null=True, blank=True)          # Дата рождения
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
    equipment = models.TextField()
    price_per_hour = models.DecimalField(max_digits=10, decimal_places=2)
    image = models.ImageField(upload_to='rooms/', blank=True, null=True)
    is_active = models.BooleanField(default=True)
    amenities = models.JSONField(default=list, blank=True)

    def __str__(self):
        return self.name

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

    user = models.ForeignKey(User, on_delete=models.CASCADE)
    room = models.ForeignKey(Room, on_delete=models.CASCADE)
    start_time = models.DateTimeField()
    end_time = models.DateTimeField()
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='pending')
    created_at = models.DateTimeField(auto_now_add=True)
    participants_count = models.IntegerField(default=1)  # ★★★ кол-во участников
    description = models.TextField(blank=True)  # ★★★ описание встречи

    def __str__(self):
        return f"{self.user.username} - {self.room.name} - {self.start_time.strftime('%d.%m.%Y %H:%M')}"