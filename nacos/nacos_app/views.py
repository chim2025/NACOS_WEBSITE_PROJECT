from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login, logout
from django.http import JsonResponse
from django.contrib.auth.decorators import login_required
from django.views.decorators.csrf import csrf_protect
from django.views.decorators.http import require_POST
from django.views.decorators.csrf import csrf_protect, ensure_csrf_cookie
from django.core.files.base import ContentFile
from django.contrib import messages
import base64
import json
from django.core.exceptions import ValidationError
from .models import CustomUser

@csrf_protect
def login_view(request):
    if request.user.is_authenticated:
        if request.user.is_migrated and not request.user.has_usable_password():
            return redirect('set_password')
        return redirect('dashboard')
    
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
                'message': 'Login successful.',
                'show_profile_upload': not user.profile_picture
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
    context = {
        'messages': messages.get_messages(request),
        'active_tab': 'home',
        'show_profile_upload': not request.user.profile_picture
    }
    return render(request, 'dashboard.html', context)

@login_required
@require_POST
@csrf_protect
def upload_profile_picture(request):
    try:
        data = request.POST.get('image')
        if not data:
            return JsonResponse({
                'success': False,
                'message': 'No image data provided.'
            }, status=400)

        image_array_1 = data.split(";")
        if len(image_array_1) < 2:
            return JsonResponse({
                'success': False,
                'message': 'Invalid image format.'
            }, status=400)

        image_array_2 = image_array_1[1].split(",")
        if len(image_array_2) < 2:
            return JsonResponse({
                'success': False,
                'message': 'Invalid base64 data.'
            }, status=400)

        base64_data = image_array_2[1]
        try:
            image_data = base64.b64decode(base64_data)
        except base64.binascii.Error:
            return JsonResponse({
                'success': False,
                'message': 'Invalid base64 encoding.'
            }, status=400)

        user = request.user
        filename = f'{user.username}_profile.png'
        user.profile_picture.save(filename, ContentFile(image_data))
        user.save()

        return JsonResponse({
            'success': True,
            'message': 'Profile picture uploaded successfully.',
            'image_url': user.profile_picture.url if user.profile_picture else None
        })

    except Exception as e:
        return JsonResponse({
            'success': False,
            'message': f'Error uploading profile picture: {str(e)}'
        }, status=500)
@login_required
@require_POST
@csrf_protect
def edit_profile(request):
    try:
        # Parse JSON data from request body
        data = json.loads(request.body)
        
        # Define allowed fields for editing
        allowed_fields = [
            'first_name', 'surname', 'other_names', 'phone', 'address', 'lga', 
            'state', 'sex', 'hobby', 'denomination', 'parent_phone', 'mother_name', 
            'room', 'course'
        ]
        
        # Get the authenticated user
        user = request.user
        
        # Update only allowed fields that are provided in the request
        updated_fields = []
        for field in allowed_fields:
            if field in data:
                value = data[field]
                # Handle empty strings as None for optional fields
                if value == '':
                    value = None
                setattr(user, field, value)
                updated_fields.append(field)
        
        # Validate the updated user data
        try:
            user.full_clean()  # Runs model validation
        except ValidationError as e:
            error_messages = []
            for field, errors in e.message_dict.items():
                error_messages.append(f"{field}: {', '.join(errors)}")
            return JsonResponse({
                'success': False,
                'message': f"Validation error: {'; '.join(error_messages)}"
            }, status=400)
        
        # Save the user
        user.save()
        
        return JsonResponse({
            'success': True,
            'message': f"Profile updated successfully. Updated fields: {', '.join(updated_fields) or 'None'}",
            'updated_data': {
                field: getattr(user, field) for field in allowed_fields
            }
        })
    
    except json.JSONDecodeError:
        return JsonResponse({
            'success': False,
            'message': 'Invalid JSON data.'
        }, status=400)
    except Exception as e:
        return JsonResponse({
            'success': False,
            'message': f'Error updating profile: {str(e)}'
        }, status=500)

def logout_view(request):
    logout(request)
    request.session.flush()
    messages.success(request, 'Logged out successfully.')
    return redirect('login')

@ensure_csrf_cookie
@csrf_protect
def check_session(request):
    return JsonResponse({
        'is_authenticated': request.user.is_authenticated,
        'username': request.user.username if request.user.is_authenticated else None,
        'is_migrated': request.user.is_migrated if request.user.is_authenticated else False,
        'has_usable_password': request.user.has_usable_password() if request.user.is_authenticated else False,
        'show_profile_upload': not request.user.profile_picture if request.user.is_authenticated else False,
        'profile': {
            'first_name': request.user.first_name,
            'surname': request.user.surname,
            'other_names': request.user.other_names,
            'phone': request.user.phone,
            'address': request.user.address,
            'lga': request.user.lga,
            'state': request.user.state,
            'sex': request.user.sex,
            'hobby': request.user.hobby,
            'denomination': request.user.denomination,
            'parent_phone': request.user.parent_phone,
            'mother_name': request.user.mother_name,
            'room': request.user.room,
            'course': request.user.course,
            'profile_picture': request.user.profile_picture.url if request.user.profile_picture else None
        } if request.user.is_authenticated else None
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