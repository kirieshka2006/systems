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

    # Техподдержка
    path('support/', views.support_view, name='support'),
    path('support/create-ticket/', views.create_ticket, name='create_ticket'),
    path('support/ticket/<int:ticket_id>/', views.ticket_detail, name='ticket_detail'),
    path('support/ticket/<int:ticket_id>/close/', views.close_ticket, name='close_ticket'),
    path('support/ticket/<int:ticket_id>/check-status/', views.check_ticket_status, name='check_ticket_status'),
    path('support/ticket/<int:ticket_id>/delete/', views.delete_ticket, name='delete_ticket'),

    path('api/available-rooms/', views.get_available_rooms, name='available_rooms'),
    path('api/create-booking/', views.create_booking, name='create_booking'),

    path('room-management/', views.room_management_main, name='room_management_main'),
    path('room-management/<str:category>/', views.room_management_category, name='room_management_category'),
    path('api/add-room/', views.add_room, name='add_room'),
    path('api/edit-room/<int:room_id>/', views.edit_room, name='edit_room'),
    path('api/delete-room/<int:room_id>/', views.delete_room, name='delete_room'),
    path('api/get-room/<int:room_id>/', views.get_room_data, name='get_room_data'),
    path('api/get-all-rooms/', views.get_all_rooms, name='get_all_rooms'),
    path('api/toggle-room-status/<int:room_id>/', views.toggle_room_status, name='toggle_room_status'),


    path('api/update-booking-status/<int:booking_id>/', views.update_booking_status, name='update_booking_status'),
    path('api/available-times/<int:room_id>/', views.get_available_times, name='available_times'),
    path('api/delete-booking/<int:booking_id>/', views.delete_booking, name='delete_booking'),

    path('api/delete-user/<int:user_id>/', views.delete_user, name='delete_user'),

    path('booking-history/', views.booking_history, name='booking_history'),

    path('offices/', views.offices_view, name='offices'),
    path('office-management/', views.office_management, name='office_management'),
    path('office-management/add/', views.add_office, name='add_office'),
    path('office-management/<int:office_id>/edit/', views.edit_office, name='edit_office'),
    path('office-management/<int:office_id>/delete/', views.delete_office, name='delete_office'),

    path("api/change-role/<int:user_id>/", views.change_user_role, name="change_user_role"),


]

urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)