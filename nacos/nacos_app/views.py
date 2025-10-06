from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login, logout
from django.http import JsonResponse
from django.contrib.auth.decorators import login_required
from django.views.decorators.csrf import csrf_protect
from django.contrib import messages
from .models import CustomUser

@csrf_protect
def login_view(request):
    #if request.user.is_authenticated:
        #if request.user.is_migrated and not request.user.has_usable_password():
            #return redirect('set_password')
       # return redirect('dashboard')
    
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        user = authenticate(request, username=username, password=password)
        
        if user is not None:
            login(request, user)
            if user.is_migrated and not user.has_usable_password():
                messages.success(request, 'Please set a new password.')
                return JsonResponse({
                    'success': True,
                    'redirect_url': '/set-password/',
                    'message': 'Please set a new password.'
                })
            messages.success(request, 'Login successful.')
            return JsonResponse({
                'success': True,
                'redirect_url': '/dashboard/',
                'message': 'Login successful.'
            })
        messages.error(request, 'Invalid NACOS ID, email, or matric number, or incorrect password.')
        return JsonResponse({
            'success': False,
            'message': 'Invalid NACOS ID, email, or matric number, or incorrect password.'
        }, status=400)
    
    return render(request, 'code.html', {'messages': messages.get_messages(request)})

@csrf_protect
def set_password_view(request):
    if not request.user.is_authenticated:
        messages.error(request, 'Please log in to set your password.')
        return redirect('login')
    
    if request.method == 'POST':
        password = request.POST.get('password')
        confirm_password = request.POST.get('confirm_password')
        
        if password and confirm_password and password == confirm_password:
            user = request.user
            user.set_password(password)
            user.is_migrated = False
            user.save()
            logout(request)
            request.session.flush()
            messages.success(request, 'Password set successfully. Please log in.')
            return JsonResponse({
                'success': True,
                'redirect_url': '/login/',
                'message': 'Password set successfully.'
            })
        messages.error(request, 'Passwords do not match or are invalid.')
        return JsonResponse({
            'success': False,
            'message': 'Passwords do not match or are invalid.'
        }, status=400)
    
    return render(request, 'set_password.html', {'messages': messages.get_messages(request)})

@login_required
def dashboard_view(request):
    return render(request, 'dashboard.html', {'messages': messages.get_messages(request), 'active_tab': 'home'})

def logout_view(request):
    logout(request)
    request.session.flush()
    messages.success(request, 'Logged out successfully.')
    return redirect('login')

@csrf_protect
def check_session(request):
    return JsonResponse({
        'is_authenticated': request.user.is_authenticated,
        'username': request.user.username if request.user.is_authenticated else None,
        'is_migrated': request.user.is_migrated if request.user.is_authenticated else False,
        'has_usable_password': request.user.has_usable_password() if request.user.is_authenticated else False
    })

@csrf_protect
def admin_login_view(request):
    if request.user.is_authenticated and request.user.is_staff:
        return redirect('admin:index')
    
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        user = authenticate(request, username=username, password=password)
        
        if user is not None and user.is_staff:
            login(request, user)
            messages.success(request, 'Admin login successful.')
            return JsonResponse({
                'success': True,
                'redirect_url': '/admin/',
                'message': 'Admin login successful.'
            })
        messages.error(request, 'Invalid credentials or not an admin.')
        return JsonResponse({
            'success': False,
            'message': 'Invalid credentials or not an admin.'
        }, status=400)
    
    return render(request, 'adminlogin.html', {'messages': messages.get_messages(request)})