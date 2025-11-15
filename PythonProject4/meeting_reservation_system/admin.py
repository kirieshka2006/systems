from django.contrib import admin
from .models import User, Room, Booking, SupportTicket, TicketResponse, FAQ


@admin.register(User)
class UserAdmin(admin.ModelAdmin):
    list_display = ['username', 'email', 'role', 'phone']


@admin.register(SupportTicket)
class SupportTicketAdmin(admin.ModelAdmin):
    list_display = ['id', 'user', 'subject', 'status', 'created_at']
    list_filter = ['status', 'created_at']
    search_fields = ['user__username', 'subject']


@admin.register(TicketResponse)
class TicketResponseAdmin(admin.ModelAdmin):
    list_display = ['ticket', 'user', 'created_at']

@admin.register(FAQ)
class FAQAdmin(admin.ModelAdmin):
    list_display = ['question', 'category', 'order', 'is_active']
    list_filter = ['category', 'is_active']
    search_fields = ['question', 'answer']

@admin.register(Room)
class RoomAdmin(admin.ModelAdmin):
    list_display = ['name', 'category', 'status', 'capacity', 'price_per_hour', 'is_active']
    list_filter = ['category', 'status', 'is_active']
    search_fields = ['name', 'location']

    fieldsets = [
        ('Основная информация', {
            'fields': ['name', 'category', 'status', 'is_active']
        }),
        ('Характеристики', {
            'fields': ['capacity', 'price_per_hour', 'location', 'image']
        }),
        ('Оборудование', {
            'fields': ['equipment'],
            'description': 'Вводите каждый пункт оборудования с новой строки. Например:<br>'
                           '- Проектор<br>- Маркерная доска<br>- Wi-Fi<br>- Кондиционер'
        }),
        ('Дополнительно', {
            'fields': ['amenities'],
            'classes': ['collapse']
        }),
    ]

    def get_queryset(self, request):
        return super().get_queryset(request).select_related()


@admin.register(Booking)
class BookingAdmin(admin.ModelAdmin):
    list_display = ['user', 'room', 'start_time', 'end_time', 'status']
    list_filter = ['status', 'start_time']
    search_fields = ['user__username', 'room__name']