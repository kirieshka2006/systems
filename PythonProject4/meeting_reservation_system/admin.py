from django.contrib import admin
from .models import User, Room, Booking

@admin.register(User)
class UserAdmin(admin.ModelAdmin):
    list_display = ['username', 'email', 'role', 'phone']

@admin.register(Room)
class RoomAdmin(admin.ModelAdmin):
    list_display = ['name', 'location', 'capacity', 'price_per_hour']

@admin.register(Booking)
class BookingAdmin(admin.ModelAdmin):
    list_display = ['user', 'room', 'start_time', 'end_time', 'status']