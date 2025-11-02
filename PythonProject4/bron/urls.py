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
]
urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)