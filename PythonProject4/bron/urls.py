from django.contrib import admin
from django.urls import path
from meeting_reservation_system import views
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', views.home, name='home'),
    path('register/', views.register, name='register'),
    path('login/', views.login_view, name='login'),
    path('room/<int:room_id>/', views.room_detail, name='room_detail'),
    path('logout/', views.logout_view, name='logout'),
    path('profile/', views.profile_view, name='profile'),
    path('profile/update/', views.update_profile, name='update_profile'),
    path('profile/change_password/', views.change_password, name='change_password'),
    path('profile/update_avatar/', views.update_avatar, name='update_avatar'),
    path('profile/verify-email/', views.verify_email, name='verify_email'),
    path('recovery/', views.recovery_view, name='recovery'),
    path('login/success/', views.login_success_view, name='login_with_success'),
    path('admin-panel/', views.admin_panel, name='admin_panel'),
    path('manager-panel/', views.manager_panel, name='manager_panel'),
    path('admin-panel/user/<int:user_id>/', views.admin_user_profile, name='admin_user_profile'),
    path('info/', views.info_page, name='info'),

    path('api/available-rooms/', views.get_available_rooms, name='available_rooms'),
    path('api/create-booking/', views.create_booking, name='create_booking'),


    path('room-management/', views.room_management_main, name='room_management_main'),
    path('room-management/<str:category>/', views.room_management_category, name='room_management_category'),  # Страница категории
    path('api/add-room/', views.add_room, name='add_room'),
    path('api/edit-room/<int:room_id>/', views.edit_room, name='edit_room'),
    path('api/delete-room/<int:room_id>/', views.delete_room, name='delete_room'),
    path('api/get-room/<int:room_id>/', views.get_room_data, name='get_room_data'),
    path('api/get-all-rooms/', views.get_all_rooms, name='get_all_rooms'),
    path('api/toggle-room-status/<int:room_id>/', views.toggle_room_status, name='toggle_room_status'),

    path('api/booking-form/<int:room_id>/', views.booking_form, name='booking_form'),
]
urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)