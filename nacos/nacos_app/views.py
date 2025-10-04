from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login
from django.contrib import messages
from django.http import JsonResponse
from nacos_app.models import CustomUser

def login_view(request):
    if request.user.is_authenticated:
        return redirect('dashboard')
    
    if request.method == 'POST' and request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        username = request.POST.get('username')
        password = request.POST.get('password')
        user = authenticate(request, username=username, password=password)
        if user is not None:
            login(request, user)
            return JsonResponse({'status': 'success', 'message': f'Welcome back, {user.username}!', 'redirect': '/dashboard/'})
        else:
            try:
                user = CustomUser.objects.get(username=username)
                if user.has_unusable_password() or user.is_migrated:
                    request.session['user_to_set_password'] = user.id
                    return JsonResponse({'status': 'set_password', 'message': 'Please create a new password.', 'redirect': '/set-password/'})
            except CustomUser.DoesNotExist:
                pass
            return JsonResponse({'status': 'error', 'message': 'Invalid username or password.'}, status=400)
    
    return render(request, 'code.html')

def admin_login_view(request):
    if request.user.is_authenticated and request.user.is_staff:
        return redirect('admin:index')
    
    if request.method == 'POST' and request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        username = request.POST.get('username')
        password = request.POST.get('password')
        user = authenticate(request, username=username, password=password)
        if user is not None and user.is_staff:
            login(request, user)
            return JsonResponse({'status': 'success', 'message': f'Welcome, Admin {user.username}!', 'redirect': '/admin/'})
        return JsonResponse({'status': 'error', 'message': 'Invalid admin credentials or not an admin.'}, status=400)
    
    return render(request, 'adminlogin.html')

def set_password_view(request):
    if 'user_to_set_password' not in request.session:
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return JsonResponse({'status': 'error', 'message': 'Invalid session. Please try logging in again.', 'redirect': '/login/'}, status=400)
        messages.error(request, 'Invalid session. Please try logging in again.')
        return redirect('login')
    
    user_id = request.session.get('user_to_set_password')
    try:
        user = CustomUser.objects.get(id=user_id)
    except CustomUser.DoesNotExist:
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return JsonResponse({'status': 'error', 'message': 'User not found. Please try again.', 'redirect': '/login/'}, status=400)
        messages.error(request, 'User not found. Please try again.')
        return redirect('login')
    
    if request.method == 'POST' and request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        password1 = request.POST.get('password1')
        password2 = request.POST.get('password2')
        if password1 and password2 and password1 == password2:
            user.set_password(password1)
            user.is_migrated = False
            user.save()
            del request.session['user_to_set_password']
            return JsonResponse({'status': 'success', 'message': 'Password set successfully. Please log in.', 'redirect': '/login/'})
        return JsonResponse({'status': 'error', 'message': 'Passwords do not match or are invalid.'}, status=400)
    
    return render(request, 'nacos_app/set_password.html')

def dashboard_view(request):
    if not request.user.is_authenticated:
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return JsonResponse({'status': 'error', 'message': 'Please log in to access the dashboard.', 'redirect': '/login/'}, status=401)
        messages.info(request, 'Please log in to access the dashboard.')
        return redirect('login')
    return render(request, 'nacos_app/dashboard.html', {'user': request.user})