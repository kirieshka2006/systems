from django.shortcuts import render, redirect
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth import login, authenticate, logout  # ← Добавил logout
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.auth import update_session_auth_hash
from django.core.files.storage import FileSystemStorage
from django.utils import timezone
from .models import Room, User, EmailConfirmation, Booking
from django.http import JsonResponse
from datetime import datetime, timedelta
from .models import SupportTicket, TicketResponse
import json
from decimal import Decimal
@login_required
def ticket_response_form(request, ticket_id):
    """Возвращает HTML форму для ответа на тикет"""
    try:
        ticket = SupportTicket.objects.get(id=ticket_id)
        return render(request, 'ticket_response_form.html', {'ticket': ticket})
    except SupportTicket.DoesNotExist:
        return JsonResponse({'error': 'Тикет не найден'}, status=404)

def support_view(request):
    """Страница техподдержки"""
    context = {
        'my_tickets': SupportTicket.objects.filter(user=request.user).order_by(
            '-created_at') if request.user.is_authenticated else [],
    }

    if request.user.is_authenticated and request.user.role in ['admin', 'manager']:
        context['all_tickets'] = SupportTicket.objects.all().order_by('-created_at')

    return render(request, 'support.html', context)


@login_required
def create_ticket(request):
    """Создание нового тикета"""
    if request.method == 'POST':
        subject = request.POST.get('subject')
        message = request.POST.get('message')

        ticket = SupportTicket.objects.create(
            user=request.user,
            subject=subject,
            message=message
        )
        messages.success(request, '✅ Ваш вопрос отправлен в техподдержку!')

        # ★★★ ПРАВИЛЬНЫЙ РЕДИРЕКТ С ЯКОРЕМ ★★★
        from django.http import HttpResponseRedirect
        from django.urls import reverse
        return HttpResponseRedirect(reverse('support') + '#my-tickets')

    return redirect('support')


def support_view(request):
    """Страница техподдержки с FAQ"""
    from .models import FAQ
    context = {
        'my_tickets': SupportTicket.objects.filter(user=request.user).order_by(
            '-created_at') if request.user.is_authenticated else [],
        'faqs': FAQ.objects.filter(is_active=True),
        'faq_categories': FAQ.CATEGORY_CHOICES,  # ★★★ ДОБАВИЛ КАТЕГОРИИ ★★★
    }

    if request.user.is_authenticated and request.user.role in ['admin', 'manager']:
        context['all_tickets'] = SupportTicket.objects.all().order_by('-created_at')

    return render(request, 'support.html', context)

@login_required
def ticket_detail(request, ticket_id):
    """Детальная страница тикета"""
    try:
        ticket = SupportTicket.objects.get(id=ticket_id)

        # Проверяем доступ - разрешаем автору и менеджерам/админам
        if ticket.user != request.user and request.user.role not in ['admin', 'manager']:
            messages.error(request, '❌ Доступ запрещен!')
            return redirect('support')

        if request.method == 'POST':
            response_text = request.POST.get('response')
            if response_text:
                # Проверяем что тикет не закрыт
                if ticket.status == 'closed':
                    messages.error(request, '❌ Тикет закрыт! Новые ответы невозможны.')
                    return redirect('support')

                TicketResponse.objects.create(
                    ticket=ticket,
                    user=request.user,
                    message=response_text
                )

                # Обновляем статус и активность
                if request.user.role in ['admin', 'manager']:
                    ticket.status = 'in_progress'
                ticket.last_activity = timezone.now()
                ticket.save()

                messages.success(request, '✅ Ответ отправлен!')

        return render(request, 'ticket_detail.html', {'ticket': ticket})

    except SupportTicket.DoesNotExist:
        messages.error(request, '❌ Обращение не найдено!')
        return redirect('support')

@login_required
def update_ticket_status(request, ticket_id):
    """Обновление статуса тикета (для менеджеров)"""
    if request.user.role not in ['admin', 'manager']:
        return JsonResponse({'success': False, 'error': 'Доступ запрещен'})

    try:
        ticket = SupportTicket.objects.get(id=ticket_id)
        new_status = request.POST.get('status')
        if new_status in dict(SupportTicket.STATUS_CHOICES):
            ticket.status = new_status
            ticket.save()
            return JsonResponse({'success': True})
    except SupportTicket.DoesNotExist:
        pass

    return JsonResponse({'success': False, 'error': 'Ошибка обновления'})


@login_required
def close_ticket(request, ticket_id):
    """Закрытие тикета пользователем"""
    try:
        ticket = SupportTicket.objects.get(id=ticket_id)

        # Проверяем что пользователь является автором тикета
        if ticket.user != request.user:
            messages.error(request, '❌ Вы можете закрывать только свои обращения!')
            return redirect('support')

        # Меняем статус на закрытый
        ticket.status = 'closed'
        ticket.save()

        messages.success(request, '✅ Тикет закрыт! Спасибо за обращение.')
        return redirect('support')

    except SupportTicket.DoesNotExist:
        messages.error(request, '❌ Обращение не найдено!')
        return redirect('support')


@login_required
def delete_ticket(request, ticket_id):
    """Удаление тикета менеджером/админом"""
    if request.user.role not in ['admin', 'manager']:
        return JsonResponse({'success': False, 'error': 'Доступ запрещен'})

    try:
        ticket = SupportTicket.objects.get(id=ticket_id)

        # ★★★ ПРОВЕРЯЕМ ЧТО ТИКЕТ НЕ В СТАТУСЕ "ОТКРЫТ" ★★★
        if ticket.status == 'open':
            return JsonResponse({'success': False, 'error': 'Нельзя удалять открытые тикеты'})

        ticket.delete()
        return JsonResponse({'success': True})

    except SupportTicket.DoesNotExist:
        return JsonResponse({'success': False, 'error': 'Тикет не найден'})

@login_required
def check_ticket_status(request, ticket_id):
    """Проверка статуса тикета для AJAX"""
    try:
        ticket = SupportTicket.objects.get(id=ticket_id)
        return JsonResponse({'status': ticket.status})
    except SupportTicket.DoesNotExist:
        return JsonResponse({'status': 'not_found'})



def login_view(request):
    """Вход в систему (ТОЛЬКО вход)"""
    success_message = request.session.pop('recovery_success_message', None)
    if success_message:
        messages.success(request, success_message)

    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')

        user = authenticate(request, username=username, password=password)

        if user is not None:
            login(request, user)
            return redirect('home')
        else:
            # Обычная обработка ошибки
            user_exists = User.objects.filter(username=username).exists()
            if user_exists:
                messages.error(request, 'Неправильный пароль!')
                return render(request, 'login.html', {'username_value': username})
            else:
                messages.error(request, 'Пользователь с таким логином не найден!')
                return render(request, 'login.html', {'username_value': ''})

    return render(request, 'login.html')


def recovery_view(request):
    """Страница восстановления пароля"""
    if request.method == 'POST':
        form_type = request.POST.get('form_type', 'recovery_email')
        print("DEBUG: recovery_view вызван")
        # ★★★ ОБРАБОТКА ВВОДА EMAIL ★★★
        if form_type == 'recovery_email':
            email = request.POST.get('recovery_email')
            print(f"DEBUG: recovery_email = {email}")
            # Ищем пользователя с email
            try:
                user = User.objects.get(email=email)

                # Отправляем код восстановления
                from .email_utils import send_recovery_code
                code = send_recovery_code(user, email)

                # Сохраняем в сессии
                request.session['recovery_user_id'] = user.id
                request.session['recovery_email'] = email

                messages.info(request, f'📧 Код восстановления отправлен на {email}')
                return render(request, 'recovery.html', {
                    'show_recovery_code': True,
                    'recovery_email': email
                })

            except User.DoesNotExist:
                messages.error(request, '❌ Аккаунт с таким email не найден!')
                return render(request, 'recovery.html')

        # ★★★ ОБРАБОТКА КОДА ВОССТАНОВЛЕНИЯ ★★★
        elif form_type == 'recovery_code':
            return handle_password_recovery(request)

    return render(request, 'recovery.html')

def logout_view(request):
    """Выход из системы"""
    # Очищаем все старые сообщения
    storage = messages.get_messages(request)
    for message in storage:
        pass  # Просто очищаем все сообщения

    logout(request)
    messages.success(request, 'Вы успешно вышли из системы!')
    return redirect('home')


def handle_password_recovery(request):
    """Обрабатывает восстановление пароля по коду"""
    recovery_code = request.POST.get('recovery_code')
    new_password = request.POST.get('new_password')
    confirm_password = request.POST.get('confirm_password')

    user_id = request.session.get('recovery_user_id')
    email = request.session.get('recovery_email')

    print(f"DEBUG: recovery_code={recovery_code}, user_id={user_id}, email={email}")

    if not user_id or not email:
        messages.error(request, '❌ Сессия устарела! Начните восстановление заново.')
        return render(request, 'recovery.html')

    try:
        user = User.objects.get(id=user_id)
        confirmation = EmailConfirmation.objects.get(
            user=user,
            email=email,
            code=recovery_code,
            confirmed_at__isnull=True
        )

        if confirmation.is_expired():
            messages.error(request, '❌ Код устарел! Запросите новый.')
            return render(request, 'recovery.html', {
                'show_recovery_code': True,
                'recovery_email': email
            })

        # Проверяем пароли
        if new_password != confirm_password:
            messages.error(request, '❌ Пароли не совпадают!')
            return render(request, 'recovery.html', {
                'show_recovery_code': True,
                'recovery_email': email
            })

        if len(new_password) < 8:
            messages.error(request, '❌ Пароль должен быть не менее 8 символов!')
            return render(request, 'recovery.html', {
                'show_recovery_code': True,
                'recovery_email': email
            })

        # Меняем пароль
        user.set_password(new_password)
        user.save()

        # Подтверждаем код
        confirmation.confirmed_at = timezone.now()
        confirmation.save()

        # Очищаем сессию
        del request.session['recovery_user_id']
        del request.session['recovery_email']
        request.session['failed_attempts'] = 0

        print("DEBUG: Пароль успешно изменен, рендерим login.html с сообщением")
        # ★★★ ПРОСТО РЕНДЕРИМ С СООБЩЕНИЕМ ★★★
        messages.success(request, ' Пароль успешно изменен! Теперь войдите с новым паролем.')
        return render(request, 'login.html')

    except EmailConfirmation.DoesNotExist:
        messages.error(request, '❌ Неверный код восстановления!')
        return render(request, 'recovery.html', {
            'show_recovery_code': True,
            'recovery_email': email
        })

def login_success_view(request):
    """Страница входа с сообщением об успешной смене пароля"""
    messages.success(request, '✅ Пароль успешно изменен! Теперь войдите с новым паролем.')
    # ★★★ НЕ ДЕЛАЕМ РЕДИРЕКТ, А РЕНДЕРИМ СТРАНИЦУ ★★★
    return render(request, 'login.html')

def register(request):
    """Регистрация нового пользователя"""
    if request.method == 'POST':
        username = request.POST.get('username')
        password1 = request.POST.get('password1')
        password2 = request.POST.get('password2')

        # Проверяем что пароли совпадают
        if password1 != password2:
            messages.error(request, 'Пароли не совпадают!')
            return render(request, 'register.html')

        # Проверяем что пользователь не существует
        if User.objects.filter(username=username).exists():
            messages.error(request, 'Пользователь с таким именем уже существует!')
            return render(request, 'register.html')

        # Создаем пользователя
        try:
            user = User.objects.create_user(
                username=username,
                password=password1,
                role='user',  # По умолчанию обычный пользователь
                email_verified = False,  # ★★★ ДОБАВЬ ЭТУ СТРОКУ ★★★
                email_verification_code = '',  # ★★★ И ЭТУ ★★★
            )
            login(request, user)
            messages.success(request, 'Аккаунт успешно создан!')
            return redirect('home')
        except Exception as e:
            messages.error(request, f'Ошибка при создании аккаунта: {str(e)}')
            return render(request, 'register.html')

    return render(request, 'register.html')


def info_page(request):
    """Страница с информацией и правилами"""
    return render(request, 'info.html')


def home(request):
    """Главная страница"""
    if request.user.is_authenticated and request.user.role in ['admin', 'manager']:
        # Админы и менеджеры видят все комнаты
        rooms = Room.objects.all()
    else:
        # Обычные пользователи видят только активные комнаты
        rooms = Room.objects.filter(status='active')

    return render(request, 'home.html', {'rooms': rooms})


def room_detail(request, room_id):
    """Страница комнаты"""
    try:
        room = Room.objects.get(id=room_id)

        # Проверяем доступ для обычных пользователей
        if not request.user.is_authenticated or request.user.role not in ['admin', 'manager']:
            if room.status != 'active':
                messages.error(request, '❌ Эта комната временно недоступна!')
                return redirect('home')

        return render(request, 'room_detail.html', {'room': room})
    except Room.DoesNotExist:
        messages.error(request, '❌ Комната не найдена!')
        return redirect('home')


@login_required
def profile_view(request):
    """Страница профиля"""
    # Получаем статистику бронирований
    user_bookings_count = Booking.objects.filter(user=request.user).count()

    return render(request, 'profile.html', {
        'user': request.user,
        'bookings_count': user_bookings_count
    })


@login_required
def admin_panel(request):
    """Админ-панель управления системой"""
    # Проверяем что пользователь админ
    if request.user.role != 'admin':
        messages.error(request, '❌ Доступ запрещен!')
        return redirect('home')

    # Получаем всех пользователей для управления
    users = User.objects.all()
    return render(request, 'admin_panel.html', {'users': users})


@login_required
def manager_panel(request):
    """Менеджерская панель для подтверждения бронирований"""
    if request.user.role not in ['manager', 'admin']:
        messages.error(request, '❌ Доступ запрещен!')
        return redirect('home')

    bookings = Booking.objects.all().order_by('-created_at')
    rooms = Room.objects.all()

    from django.utils.timezone import get_current_timezone

    for booking in bookings:
        tz = get_current_timezone()
        local_start = booking.start_time.astimezone(tz)
        local_end = booking.end_time.astimezone(tz)

        # Сохраняем как строки чтобы избежать конвертации в шаблоне
        booking.date_display = local_start.strftime("%d.%m.%Y")
        booking.time_display = f"{local_start.strftime('%H:%M')} - {local_end.strftime('%H:%M')}"

        # ★★★ НЕ присваиваем duration_hours и total_price - они теперь свойства ★★★

    return render(request, 'manager_panel.html', {
        'bookings': bookings,
        'rooms': rooms
    })


@login_required
def delete_booking(request, booking_id):
    """Удаление бронирования (для менеджеров)"""
    if request.user.role not in ['admin', 'manager']:
        return JsonResponse({'success': False, 'error': 'Доступ запрещен'})

    try:
        booking = Booking.objects.get(id=booking_id)
        booking.delete()

        messages.success(request, '✅ Бронирование успешно удалено!')
        return JsonResponse({'success': True})

    except Booking.DoesNotExist:
        return JsonResponse({'success': False, 'error': 'Бронирование не найдено'})

@login_required
def update_booking_status(request, booking_id):
    if request.user.role not in ['admin', 'manager']:
        return JsonResponse({'success': False, 'error': 'Нет доступа'})

    try:
        booking = Booking.objects.get(id=booking_id)
        data = json.loads(request.body)

        new_status = data.get('status')
        new_price = data.get('total_price')
        manager_comment = data.get('manager_comment')

        # ★★★ СОХРАНЯЕМ ИЗМЕНЕННУЮ ЦЕНУ ★★★
        if new_price:
            booking.custom_price = Decimal(new_price)

        # Менеджер оставил комментарий
        if manager_comment is not None:
            booking.manager_comment = manager_comment

        # Меняем статус
        if new_status in dict(Booking.STATUS_CHOICES):
            booking.status = new_status

        booking.save()

        # Если подтверждено — отправляем письмо с ПРАВИЛЬНОЙ ценой
        if new_status == "confirmed":
            from .email_booking import send_booking_confirmation
            send_booking_confirmation(booking)

        return JsonResponse({'success': True})

    except Booking.DoesNotExist:
        return JsonResponse({'success': False, 'error': 'Бронь не найдена'})

@login_required
def admin_user_profile(request, user_id):
    """Просмотр профиля пользователя для админа"""
    # Разрешаем админам, менеджерам и суперпользователям
    if request.user.role not in ['admin', 'manager'] and not request.user.is_superuser:
        messages.error(request, '❌ Доступ запрещен!')
        return redirect('admin_panel')  # Редирект на админ-панель вместо главной

    try:
        user = User.objects.get(id=user_id)
        return render(request, 'admin_user_profile.html', {'target_user': user})
    except User.DoesNotExist:
        messages.error(request, '❌ Пользователь не найден!')
        return redirect('admin_panel')

@login_required
def update_profile(request):
    """Обновление данных профиля"""
    if request.method == 'POST':
        user = request.user
        username = request.POST.get('username')
        phone = request.POST.get('phone')
        avatar = request.FILES.get('avatar')

        # ★★★ НОВЫЕ ПОЛЯ ★★★
        first_name = request.POST.get('first_name')
        last_name = request.POST.get('last_name')
        patronymic = request.POST.get('patronymic')
        birth_date = request.POST.get('birth_date')
        gender = request.POST.get('gender')

        # Проверяем username
        if username and username != user.username:
            if User.objects.filter(username=username).exclude(id=user.id).exists():
                messages.error(request, '❌ Это имя пользователя уже занято!')
                return redirect('profile')
            user.username = username

        # Сохраняем телефон
        if phone is not None:
            user.phone = phone

        # ★★★ СОХРАНЯЕМ НОВЫЕ ПОЛЯ ★★★
        user.first_name = first_name
        user.last_name = last_name
        user.patronymic = patronymic
        user.gender = gender

        if birth_date:
            user.birth_date = birth_date

        # Сохраняем аватар
        if avatar:
            fs = FileSystemStorage(location='media/avatars/')
            filename = fs.save(avatar.name, avatar)
            user.avatar = f'avatars/{filename}'

        # Сохраняем пользователя
        try:
            user.save()
            messages.success(request, '✅ Профиль успешно обновлён!')
        except Exception as e:
            messages.error(request, f'❌ Ошибка при обновлении профиля: {str(e)}')

        return redirect('profile')
    return redirect('profile')


@login_required
def verify_email(request):
    """Подтверждение email"""
    if request.method == 'POST':
        user = request.user
        email = request.POST.get('email')
        confirmation_code = request.POST.get('confirmation_code')

        # Если отправляем код
        if email and not confirmation_code:
            # Проверяем не занят ли email другим пользователем
            if User.objects.filter(email=email).exclude(id=user.id).exists():
                messages.error(request, '❌ Этот email уже используется!')
                return redirect('profile')

            # Отправляем код подтверждения
            from .email_utils import send_confirmation_code
            try:
                code = send_confirmation_code(user, email)
                messages.info(request, f'📧 Код подтверждения отправлен на {email}!')
                print(f"КОД ДЛЯ ТЕСТА: {code}")
                # Сохраняем email во временную переменную сессии
                request.session['pending_email'] = email
            except Exception as e:
                messages.error(request, f'❌ Ошибка отправки кода: {str(e)}')

        # Если вводим код
        elif confirmation_code:
            pending_email = request.session.get('pending_email')
            if not pending_email:
                messages.error(request, '❌ Сначала укажите email и отправьте код!')
                return redirect('profile')

            try:
                confirmation = EmailConfirmation.objects.get(
                    user=user,
                    code=confirmation_code,
                    confirmed_at__isnull=True
                )

                if confirmation.is_expired():
                    messages.error(request, '❌ Код устарел! Запросите новый.')
                else:
                    # Подтверждаем email и сохраняем
                    confirmation.confirmed_at = timezone.now()
                    confirmation.save()
                    user.email = pending_email
                    user.save()
                    # Очищаем временные данные
                    del request.session['pending_email']
                    messages.success(request, '✅ Email успешно подтвержден и сохранен!')

            except EmailConfirmation.DoesNotExist:
                messages.error(request, '❌ Неверный код подтверждения!')

        return redirect('profile')
    return redirect('profile')




@login_required
def get_available_rooms(request):
    """AJAX: Получить доступные комнаты"""
    date = request.GET.get('date')
    start_time = request.GET.get('start_time')
    duration = request.GET.get('duration')
    participants = request.GET.get('participants')

    # Здесь логика проверки доступности комнат
    rooms = Room.objects.filter(is_active=True)

    # Фильтрация по вместимости
    if participants and int(participants) > 0:
        rooms = rooms.filter(capacity__gte=int(participants))

    # TODO: Проверка занятости по времени
    available_rooms = []
    for room in rooms:
        available_rooms.append({
            'id': room.id,
            'name': room.name,
            'capacity': room.capacity,
            'location': room.location,
            'price_per_hour': room.price_per_hour,
            'amenities': room.amenities
        })

    return JsonResponse({'rooms': available_rooms})


@login_required
def create_booking(request):
    """Создать бронирование со страницы комнаты"""
    if request.method == 'POST':
        try:
            room_id = request.POST.get('room_id')
            date_str = request.POST.get('selected_date')
            time_str = request.POST.get('start_time')
            duration = request.POST.get('duration')
            full_name = request.POST.get('full_name')
            phone = request.POST.get('phone')
            email = request.POST.get('email')
            comment = request.POST.get('comment')

            print(
                f"🔍 ДЕБАГ: Получены данные - комната:{room_id}, дата:{date_str}, время:{time_str}, длительность:{duration}")

            # Получаем комнату
            room = Room.objects.get(id=room_id)

            # ★★★ ПРАВИЛЬНОЕ СОЗДАНИЕ DATETIME ★★★
            from django.utils.timezone import make_aware
            from zoneinfo import ZoneInfo

            naive_datetime = datetime.strptime(f"{date_str} {time_str}", "%Y-%m-%d %H:%M")
            start_datetime = make_aware(naive_datetime, timezone=ZoneInfo("Asia/Irkutsk"))
            end_datetime = start_datetime + timedelta(hours=int(duration))



            # Проверяем что бронирование в будущем
            if start_datetime < timezone.now():
                messages.error(request, '❌ Нельзя бронировать в прошлом!')
                return redirect('room_detail', room_id=room_id)

            # Проверяем доступность комнаты
            overlapping = Booking.objects.filter(
                room=room,
                start_time__lt=end_datetime,
                end_time__gt=start_datetime,
                status__in=['pending', 'confirmed']
            ).exists()

            if overlapping:
                messages.error(request, '❌ Комната уже занята в это время!')
                return redirect('room_detail', room_id=room_id)

            # Создаем бронирование
            booking = Booking.objects.create(
                user=request.user,
                room=room,
                start_time=start_datetime,
                end_time=end_datetime,
                description=comment,
                status='pending'
            )

            print(f"✅ БРОНИРОВАНИЕ СОЗДАНО УСПЕШНО!")
            print(f"   Сохранено в базе как: {booking.start_time}")

            messages.success(request, '✅ Запрос на бронирование отправлен! Ожидайте подтверждения.')
            return redirect('home')

        except Exception as e:
            print(f"❌ ОШИБКА ПРИ БРОНИРОВАНИИ: {str(e)}")
            messages.error(request, f'❌ Ошибка при бронировании: {str(e)}')
            return redirect('room_detail', room_id=room_id)

    return redirect('home')


@login_required
def get_available_times(request, room_id):
    """AJAX: Получить доступное время для комнаты на дату"""
    date_str = request.GET.get('date')

    try:
        room = Room.objects.get(id=room_id)
        selected_date = datetime.strptime(date_str, "%Y-%m-%d").date()

        # Все возможные слоты времени
        time_slots = []
        for hour in range(9, 20):
            time_slots.append(f"{hour:02d}:00")

        # Получаем бронирования
        bookings = Booking.objects.filter(
            room=room,
            start_time__date=selected_date,
            status__in=['pending', 'confirmed']
        )

        # Конвертируем в локальное время
        from django.utils.timezone import localtime

        # Создаем список занятого времени
        booked_slots = []
        for booking in bookings:
            local_start = localtime(booking.start_time)
            local_end = localtime(booking.end_time)

            current_time = local_start
            while current_time < local_end:
                time_str = current_time.strftime("%H:%M")
                booked_slots.append(time_str)
                current_time += timedelta(hours=1)

        available_slots = [slot for slot in time_slots if slot not in booked_slots]

        return JsonResponse({
            'available_times': available_slots,
            'booked_times': booked_slots
        })

    except Exception as e:
        print(f"❌ Ошибка в get_available_times: {str(e)}")
        return JsonResponse({'error': str(e)}, status=400)

    except Exception as e:
        print(f"❌ ОШИБКА в get_available_times: {str(e)}")
        return JsonResponse({'error': str(e)}, status=400)

@login_required
def update_avatar(request):
    """Обновление только аватарки"""
    if request.method == 'POST':
        user = request.user
        avatar = request.FILES.get('avatar')

        if avatar:
            fs = FileSystemStorage(location='media/avatars/')
            filename = fs.save(avatar.name, avatar)
            user.avatar = f'avatars/{filename}'
            user.save()
            messages.success(request, '✅ Аватарка успешно обновлена!')
        else:
            messages.error(request, '❌ Выберите файл для аватарки!')

        return redirect('profile')
    return redirect('profile')





@login_required
def add_room(request):
    """Добавление новой комнаты - только админ"""
    if request.user.role != 'admin':
        return JsonResponse({'success': False, 'error': 'Доступ запрещен!'})

    if request.method == 'POST':
        try:
            name = request.POST.get('name')
            location = request.POST.get('location')
            capacity = request.POST.get('capacity')
            price_per_hour = request.POST.get('price_per_hour')
            equipment = request.POST.get('equipment', '')

            room = Room.objects.create(
                name=name,
                location=location,
                capacity=capacity,
                price_per_hour=price_per_hour,
                equipment=equipment,
                is_active=True
            )

            # Обработка изображения
            image = request.FILES.get('image')
            if image:
                fs = FileSystemStorage(location='media/rooms/')
                filename = fs.save(image.name, image)
                room.image = f'rooms/{filename}'
                room.save()

            messages.success(request, '✅ Комната успешно добавлена!')
            return JsonResponse({'success': True, 'room_id': room.id})

        except Exception as e:
            return JsonResponse({'success': False, 'error': str(e)})

    return JsonResponse({'success': False, 'error': 'Неверный метод запроса'})


@login_required
def edit_room(request, room_id):
    """Редактирование комнаты - админ и менеджер"""
    if request.user.role not in ['admin', 'manager']:
        return JsonResponse({'success': False, 'error': 'Доступ запрещен!'})

    try:
        room = Room.objects.get(id=room_id)

        if request.method == 'POST':
            # Админ может менять всё, менеджер только цену и оборудование
            if request.user.role == 'admin':
                room.name = request.POST.get('name', room.name)
                room.location = request.POST.get('location', room.location)
                room.capacity = request.POST.get('capacity', room.capacity)

            room.price_per_hour = request.POST.get('price_per_hour', room.price_per_hour)
            room.equipment = request.POST.get('equipment', room.equipment)

            # Обработка изображения (только админ)
            if request.user.role == 'admin':
                image = request.FILES.get('image')
                if image:
                    fs = FileSystemStorage(location='media/rooms/')
                    filename = fs.save(image.name, image)
                    room.image = f'rooms/{filename}'

            room.save()
            messages.success(request, '✅ Комната успешно обновлена!')
            return JsonResponse({'success': True})

    except Room.DoesNotExist:
        return JsonResponse({'success': False, 'error': 'Комната не найдена'})

    return JsonResponse({'success': False, 'error': 'Неверный метод запроса'})


@login_required
def get_all_rooms(request):
    """Получить все комнаты для управления"""
    if request.user.role not in ['admin', 'manager']:
        return JsonResponse({'success': False, 'error': 'Доступ запрещен'})

    rooms = Room.objects.all()
    rooms_data = []
    for room in rooms:
        rooms_data.append({
            'id': room.id,
            'name': room.name,
            'location': room.location,
            'capacity': room.capacity,
            'price_per_hour': str(room.price_per_hour),
            'equipment': room.equipment,  # ← ВОТ ЭТО ВАЖНО
            'image': room.image.url if room.image else None
        })

    return JsonResponse({'rooms': rooms_data})
@login_required
def get_room_data(request, room_id):
    """Получить данные комнаты для редактирования"""
    try:
        room = Room.objects.get(id=room_id)
        return JsonResponse({
            'success': True,
            'room': {
                'id': room.id,
                'name': room.name,
                'location': room.location,
                'capacity': room.capacity,
                'price_per_hour': str(room.price_per_hour),
                'equipment': room.equipment
            }
        })
    except Room.DoesNotExist:
        return JsonResponse({'success': False, 'error': 'Комната не найдена'})

@login_required
def delete_room(request, room_id):
    """Удаление комнаты - только админ"""
    if request.user.role != 'admin':
        return JsonResponse({'success': False, 'error': 'Доступ запрещен!'})

    try:
        room = Room.objects.get(id=room_id)
        room.delete()
        messages.success(request, '✅ Комната успешно удалена!')
        return JsonResponse({'success': True})
    except Room.DoesNotExist:
        return JsonResponse({'success': False, 'error': 'Комната не найдена'})

@login_required
def change_password(request):
    """Изменение пароля"""
    if request.method == 'POST':
        old_password = request.POST.get('old_password')
        new_password = request.POST.get('new_password')
        confirm_password = request.POST.get('confirm_password')

        if not request.user.check_password(old_password):
            messages.error(request, '❌ Старый пароль неверен!')
        elif new_password != confirm_password:
            messages.error(request, '❌ Пароли не совпадают!')
        else:
            request.user.set_password(new_password)
            request.user.save()
            update_session_auth_hash(request, request.user)  # чтобы не разлогинивало
            messages.success(request, '🔐 Пароль успешно изменён!')
        return redirect('profile')


@login_required
def room_management_main(request):
    """Главная страница управления комнатами - выбор категории"""
    if request.user.role != 'admin':
        messages.error(request, '❌ Доступ запрещен!')
        return redirect('home')

    # Считаем комнаты по категориям
    categories = {
        'economy': Room.objects.filter(category='economy').count(),
        'standard': Room.objects.filter(category='standard').count(),
        'comfort': Room.objects.filter(category='comfort').count(),
        'vip': Room.objects.filter(category='vip').count(),
        'luxury': Room.objects.filter(category='luxury').count(),
    }

    return render(request, 'room_management_main.html', {'categories': categories})


@login_required
def room_management_category(request, category):
    """Страница управления комнатами конкретной категории"""
    if request.user.role != 'admin':
        messages.error(request, '❌ Доступ запрещен!')
        return redirect('home')

    # Проверяем валидность категории
    valid_categories = ['economy', 'standard', 'comfort', 'vip', 'luxury']
    if category not in valid_categories:
        messages.error(request, '❌ Неверная категория!')
        return redirect('room_management_main')

    rooms = Room.objects.filter(category=category)
    category_display = dict(Room.CATEGORY_CHOICES)[category]

    return render(request, 'room_management_category.html', {
        'rooms': rooms,
        'category': category,
        'category_display': category_display
    })
@login_required
def add_room(request):
    """Добавление новой комнаты - только админ"""
    if request.user.role != 'admin':
        return JsonResponse({'success': False, 'error': 'Доступ запрещен!'})

    if request.method == 'POST':
        try:
            name = request.POST.get('name')
            location = request.POST.get('location')
            capacity = request.POST.get('capacity')
            price_per_hour = request.POST.get('price_per_hour')
            equipment = request.POST.get('equipment', '')
            category = request.POST.get('category', 'standard')  # ← ДОБАВИЛ КАТЕГОРИЮ

            room = Room.objects.create(
                name=name,
                location=location,
                capacity=capacity,
                price_per_hour=price_per_hour,
                equipment=equipment,
                category=category,  # ← ДОБАВИЛ КАТЕГОРИЮ
                is_active=True
            )

            # Обработка изображения
            image = request.FILES.get('image')
            if image:
                fs = FileSystemStorage(location='media/rooms/')
                filename = fs.save(image.name, image)
                room.image = f'rooms/{filename}'
                room.save()

            messages.success(request, '✅ Комната успешно добавлена!')
            return JsonResponse({'success': True, 'room_id': room.id})

        except Exception as e:
            return JsonResponse({'success': False, 'error': str(e)})

    return JsonResponse({'success': False, 'error': 'Неверный метод запроса'})

@login_required
def toggle_room_status(request, room_id):
    """Переключение статуса комнаты (активна/скрыта)"""
    if request.user.role != 'admin':
        return JsonResponse({'success': False, 'error': 'Доступ запрещен!'})

    try:
        room = Room.objects.get(id=room_id)
        # Переключаем между активной и скрытой
        if room.status == 'active':
            room.status = 'hidden'
        else:
            room.status = 'active'
        room.save()

        return JsonResponse({'success': True, 'new_status': room.status})
    except Room.DoesNotExist:
        return JsonResponse({'success': False, 'error': 'Комната не найдена'})


@login_required
def delete_user(request, user_id):
    """Удаление пользователя (только для админа)"""
    if request.user.role != 'admin':
        return JsonResponse({'success': False, 'error': 'Доступ запрещен!'})

    try:
        user_to_delete = User.objects.get(id=user_id)

        # Нельзя удалить самого себя
        if user_to_delete.id == request.user.id:
            return JsonResponse({'success': False, 'error': 'Нельзя удалить свой аккаунт!'})

        # Нельзя удалить других админов
        if user_to_delete.role == 'admin':
            return JsonResponse({'success': False, 'error': 'Нельзя удалить администратора!'})

        user_to_delete.delete()
        return JsonResponse({'success': True})

    except User.DoesNotExist:
        return JsonResponse({'success': False, 'error': 'Пользователь не найден'})


@login_required
def booking_history(request):
    """История бронирований - ВСЕГДА только СВОИ бронирования"""
    # ★★★ ВНЕ ЗАВИСИМОСТИ ОТ РОЛИ - ПОКАЗЫВАЕМ ТОЛЬКО СВОИ БРОНИРОВАНИЯ ★★★
    bookings = Booking.objects.filter(user=request.user).order_by('-created_at')

    return render(request, 'booking_history.html', {'bookings': bookings})
