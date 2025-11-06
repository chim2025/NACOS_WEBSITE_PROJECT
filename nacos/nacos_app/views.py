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
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from .models import ContestApplication, ElectionPosition, ElectionTimeline, UserMessage, Vote
from django.contrib.auth import get_user_model
import logging
from django.shortcuts import get_object_or_404
from election_officer.models import ElectionOfficer
from django.utils import timezone
from django.db.models import Count
from django.contrib.auth import update_session_auth_hash  # ADD THIS
import json

logger = logging.getLogger(__name__)

@csrf_protect
def login_view(request):
    if request.user.is_authenticated:
        if isinstance(request.user, ElectionOfficer):
            return redirect('election_officer:officer_dashboard')
        return redirect('nacos_app:student_dashboard')
    
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        user = authenticate(request, username=username, password=password)
        if user is not None:
            login(request, user)
            request.session['auth_backend'] = user.backend  # ← ADD THIS

            if getattr(user, 'is_migrated', False) and not user.has_usable_password():
                return JsonResponse({
                    'success': True,
                    'redirect_url': '/set-password/',
                    'message': 'Please set a new password.'
                })

            return JsonResponse({
                'success': True,
                'redirect_url': '/dashboard/',
                'message': 'Login successful.',
                'show_profile_upload': not bool(user.profile_picture)
            })
            
           
        messages.error(request, 'Invalid NACOS ID, email, or matric number, or incorrect password.')
        return JsonResponse({
            'success': False,
            'message': 'Invalid NACOS ID, email, or matric number, or incorrect password.'
        }, status=400)
    
    return render(request, 'code.html', {'messages': messages.get_messages(request)})

@csrf_protect
@csrf_protect
def set_password_view(request):
    if not request.user.is_authenticated:
        messages.error(request, 'Please log in to set your password.')
        return redirect('nacos_app:login')

    if request.method == 'POST':
        password = request.POST.get('password')
        confirm_password = request.POST.get('confirm_password')

        if password and confirm_password and password == confirm_password:
            user = request.user
            user.set_password(password)
            user.is_migrated = False
            user.save()

            # RE-LOGIN WITH CORRECT BACKEND
            backend = request.session.get('auth_backend', 'nacos_app.auth_backend.CustomUserBackend')
            login(request, user, backend=backend)
            update_session_auth_hash(request, user)
            request.session.pop('auth_backend', None)

            return JsonResponse({
                'success': True,
                'redirect_url': '/dashboard/',
                'message': 'Password set successfully!'
            })

        return JsonResponse({
            'success': False,
            'message': 'Passwords do not match.'
        }, status=400)

    return render(request, 'set_password.html')



CustomUser = get_user_model()

# views.py
from .models import UserMessage

@login_required
def dashboard_view(request):
    user = request.user
    

    if hasattr(user, 'electionofficer'):
        return redirect('election_officer:officer_dashboard')

    active_tab = request.GET.get('tab', 'home')
    has_profile_picture = bool(getattr(user, 'profile_picture', None))

    # GET USER'S MESSAGES (UNREAD FIRST)
    user_messages = UserMessage.objects.filter(user=user).order_by('-is_read', '-created_at')
    approved_candidates = ContestApplication.objects.filter(
        approved=True
    ).select_related('user', 'position').order_by('position__name')
    positions = ElectionPosition.objects.filter(
        contestapplication__approved=True
    ).distinct().order_by('name')
    unread_count = UserMessage.objects.filter(user=request.user, is_read=False).count()
    

    context = {
        'messages': messages.get_messages(request),
        'active_tab': active_tab,
        'show_profile_upload': not has_profile_picture,
        'is_student': True,
        'approved_candidates': approved_candidates,
        'positions': positions,
        'user_messages': user_messages,
        'user':user # PASS TO TEMPLATE
    }
    context['unread_count'] = unread_count
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
        safe_username = user.username.replace('/', '_')

        filename = f'{safe_username}_profile.png' 

        # Save in FLAT folder
        user.profile_picture.save(filename, ContentFile(image_data), save=True)
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
    return redirect('nacos_app:login')

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

@login_required
@csrf_exempt
@require_http_methods(["POST"])
def submit_contest_application(request):
    try:
        # === GET DATA FROM FormData ===
        position_name = request.POST.get('position')
        manifesto = request.POST.get('manifesto')
        statement_of_result = request.FILES.get('statement_of_result')
        account_statement = request.FILES.get('account_statement')

        # === VALIDATE ===
        if not all([position_name, manifesto, statement_of_result, account_statement]):
            return JsonResponse({
                'success': False,
                'message': 'All fields are required: position, manifesto, and both PDFs.'
            }, status=400)

        if len(manifesto) > 200:
            return JsonResponse({
                'success': False,
                'message': 'Manifesto must be 200 characters or less.'
            }, status=400)

        # === GET POSITION FROM DB ===
        try:
            position = ElectionPosition.objects.get(name=position_name)
        except ElectionPosition.DoesNotExist:
            return JsonResponse({
                'success': False,
                'message': 'Invalid position selected.'
            }, status=400)

        # === CHECK DUPLICATE APPLICATION ===
        if ContestApplication.objects.filter(user=request.user, position=position).exists():
            return JsonResponse({
                'success': False,
                'message': 'You have already applied for this position.'
            }, status=400)

        # === SAVE APPLICATION ===
        application = ContestApplication(
            user=request.user,
            position=position,
            manifesto=manifesto,
            statement_of_result=statement_of_result,
            account_statement=account_statement,
        )
        application.save()

        # === CREATE USER MESSAGE ===
        UserMessage.objects.create(
            user=request.user,
            message_text='Your contest application has been submitted and is awaiting admin approval.'
        )

        # === SUCCESS RESPONSE ===
        return JsonResponse({
            'success': True,
            'message': 'Application submitted successfully!',
            'application_id': application.id
        })

    except Exception as e:
        logger.error(f"Contest submission error for user {request.user}: {str(e)}", exc_info=True)
        return JsonResponse({
            'success': False,
            'message': 'Server error. Please try again later.'
        }, status=500)



from .models import ElectionPosition  # <-- Import from nacos_app

@login_required
def get_positions_api(request):
    positions = ElectionPosition.objects.all().values('id', 'name', 'description')
    return JsonResponse({'positions': list(positions)})
from .models import ContestApplication

from django.utils import timezone

@login_required
def check_contest_status(request):
    # GET ACTIVE ELECTION
    election = ElectionTimeline.objects.filter(
        start_date__lte=timezone.now(),
        end_date__gte=timezone.now()
    ).first()

    # DEFAULT: NO ELECTION = ENDED
    response = {
        'applied': False,
        'approved': False,
        'rejected': False,
        'user_level': request.user.level,
        'allowedlevels': ['200', '300', '400'],
        'election_status': 'ended'  # ← DEFAULT
    }

   
    if election:
        response['election_status'] = 'ended' if election and election.end_date < timezone.now() else 'live'
    

    application = ContestApplication.objects.filter(user=request.user).first()
    if application:
        response.update({
            'applied': True,
            'approved': application.approved,
            'rejected': application.rejected,
        })

    return JsonResponse(response)

   
@login_required
def mark_message_read(request, message_id):
    if request.method == 'POST':
        msg = get_object_or_404(UserMessage, id=message_id, user=request.user)
        msg.is_read = not msg.is_read  # Toggle
        msg.save()
    return redirect('nacos_app:student_dashboard')
from django.views.decorators.http import require_POST

@login_required
@require_POST
def ajax_mark_message_read(request):
    message_id = request.POST.get('message_id')
    try:
        msg = UserMessage.objects.get(id=message_id, user=request.user)
        msg.is_read = not msg.is_read
        msg.save()
        return JsonResponse({
            'success': True,
            'is_read': msg.is_read,
            'message': 'Status updated.'
        })
    except UserMessage.DoesNotExist:
        return JsonResponse({'success': False, 'message': 'Message not found.'}, status=404)
@login_required
def get_latest_timeline(request):
    from django.utils import timezone
    latest = ElectionTimeline.objects.order_by('-created_at', '-id').first()
    if latest and latest.start_date and latest.end_date:
        local_tz = timezone.get_current_timezone()
        local_start = latest.start_date.astimezone(local_tz)
        local_end = latest.end_date.astimezone(local_tz)
        return JsonResponse({
            'success': True,
            'latest': {
                'start_date': local_start.replace(tzinfo=None).isoformat(),
                'end_date': local_end.replace(tzinfo=None).isoformat(),
            }
        })
    return JsonResponse({'success': False, 'message': 'No timeline set'})
@login_required
def get_election_data(request):
    """Return positions, candidates, and user vote status"""
    election = ElectionTimeline.objects.filter(
        start_date__lte=timezone.now(),
        end_date__gte=timezone.now()
    ).first()

    if not election:
        return JsonResponse({'error': 'No active election'}, status=400)

    user_votes = Vote.objects.filter(user=request.user, election=election)
    has_voted = user_votes.exists()
    voted_positions = list(user_votes.values_list('position_id', flat=True))

    positions = ElectionPosition.objects.all()
    applications = ContestApplication.objects.filter(approved=True)

    return JsonResponse({
        'election_id': election.id,
        'has_voted': has_voted,
        'user_level': request.user.level,
        'voted_positions': voted_positions,
        'allowedlevels':['200', '300', '400'],
        'positions': [
            {'id': p.id, 'name': p.name}
            for p in positions
        ],
        'candidates': [
            {
                'id': app.id,
                'name': f"{app.user.surname} {app.user.first_name}".strip() or app.user.username,
                'nacos_id': app.user.matric or app.user.membership_id,
                'position_id': app.position_id,
                'photo': app.user.profile_picture.url if app.user.profile_picture else None
            }
            for app in applications
        ]
    })
@login_required
@require_http_methods(["POST"])
def submit_vote(request):
    """Save votes — middleware already validated"""
    votes = getattr(request, 'validated_votes', {})
    election = getattr(request, 'active_election', None)

    if not votes or not election:
        return JsonResponse({'error': 'Invalid submission'}, status=400)

    saved_count = 0
    for position_id, candidate_id in votes.items():
        app = ContestApplication.objects.get(id=candidate_id)
        Vote.objects.create(
            user=request.user,
            candidate=app,
            position=app.position,
            election=election
        )
       
        saved_count += 1

    return JsonResponse({
        'success': True,
        'message': f'Vote submitted for {saved_count} position(s)'
    })
from django.db.models import Count

# views.py
from django.utils import timezone

@login_required
def get_live_results(request):
    # Get the most recent election (active OR ended)
    
    election = ElectionTimeline.objects.filter(
        start_date__lte=timezone.now(),
        end_date__gte=timezone.now()
    ).first()

    if not election:
        return JsonResponse({'positions': [], 'election_status': 'ended'})

    positions = ElectionPosition.objects.all()
    results = []

    for pos in positions:
        vote_counts = Vote.objects.filter(
            position=pos, election=election
        ).values('candidate').annotate(votes=Count('candidate'))

        candidates = []
        for vc in vote_counts:
            try:
                app = ContestApplication.objects.get(id=vc['candidate'])
                candidates.append({
                    'id': app.id,
                    'name': f"{app.user.surname} {app.user.first_name}".strip() or app.user.username,
                    'photo': app.user.profile_picture.url if app.user.profile_picture else None,
                    'votes': vc['votes']
                })
            except ContestApplication.DoesNotExist:
                continue

        results.append({
            'id': pos.id,
            'name': pos.name,
            'candidates': candidates
        })

    # THIS LINE IS CRITICAL
    return JsonResponse({
        'positions': results,
        'election_status': 'ended' if election.end_date < timezone.now() else 'live'
    })