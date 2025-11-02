from django.shortcuts import render, redirect
from django.contrib.auth import login, authenticate
from django.contrib.auth.forms import UserCreationForm
from .models import Room, User, EmailConfirmation
from django.contrib.auth import login, authenticate, logout  # ← Добавил logout
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.auth import update_session_auth_hash
from django.core.files.storage import FileSystemStorage
from django.utils import timezone


def login_view(request):
    """Вход в систему (ТОЛЬКО вход)"""
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

        # ★★★ ОБРАБОТКА ВВОДА EMAIL ★★★
        if form_type == 'recovery_email':
            email = request.POST.get('recovery_email')

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

    print(f"DEBUG: recovery_code={recovery_code}, user_id={user_id}, email={email}")  # ← ДОБАВЬ

    if not user_id or not email:
        messages.error(request, '❌ Сессия устарела! Начните восстановление заново.')
        return render(request, 'login.html', {'show_recovery': True})

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
            return render(request, 'recovery.html', {'show_recovery': True})

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

        print("DEBUG: Пароль успешно изменен, делаем редирект на login")
        messages.success(request, '✅ Пароль успешно изменен! Теперь войдите с новым паролем.')
        return redirect('login')

    except EmailConfirmation.DoesNotExist:
        messages.error(request, '❌ Неверный код восстановления!')
        return render(request, 'recovery.html', {
            'show_recovery_code': True,
            'recovery_email': email
        })

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



def home(request):
    """Главная страница"""
    rooms = Room.objects.all()
    return render(request, 'home.html', {'rooms': rooms})

def room_detail(request, room_id):
    """Страница комнаты"""
    room = Room.objects.get(id=room_id)
    return render(request, 'room_detail.html', {'room': room})

@login_required
def profile_view(request):
    """Страница профиля"""
    return render(request, 'profile.html', {'user': request.user})


@login_required
def update_profile(request):
    """Обновление данных профиля БЕЗ email"""
    if request.method == 'POST':
        user = request.user
        username = request.POST.get('username')
        phone = request.POST.get('phone')
        avatar = request.FILES.get('avatar')

        print(f"Данные: username={username}, phone={phone}")

        # Проверяем username
        if username and username != user.username:
            if User.objects.filter(username=username).exclude(id=user.id).exists():
                messages.error(request, '❌ Это имя пользователя уже занято!')
                return redirect('profile')
            user.username = username

        # Сохраняем телефон
        if phone is not None:
            user.phone = phone
            print(f"Телефон сохранен: {phone}")

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

