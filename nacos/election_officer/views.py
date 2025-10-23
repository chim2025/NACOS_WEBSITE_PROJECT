from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login, logout
from django.http import JsonResponse
from django.contrib.auth.decorators import login_required
from django.views.decorators.csrf import csrf_protect, csrf_exempt, csrf_protect 
from django.views.decorators.http import require_POST
from django.utils import timezone
from nacos_app.models import ContestApplication, ElectionTimeline, UserMessage
from election_officer.models import ElectionOfficer
import logging

logger = logging.getLogger(__name__)

@csrf_exempt
def officer_login(request):
    logger.debug(f"Request method: {request.method}, Data: {request.POST}, Next: {request.GET.get('next')}")
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        logger.debug(f"Attempting to authenticate: username={username}, password={password}")
        user = authenticate(request, username=username, password=password)
        logger.debug(f"Authenticated user: {user}, type: {type(user) if user else 'None'}")
        if user and isinstance(user, ElectionOfficer):
            login(request, user)
            request.session['user_id'] = user.id  # Force session update
            logger.debug(f"Login successful for {username}, session: {request.session.session_key}")
            next_url = request.POST.get('next', request.GET.get('next', 'election_officer:officer_dashboard'))
            return redirect(next_url)
        else:
            logger.debug(f"Login failed for {username}, user: {user}")
            return render(request, 'adlogin.html', {'error': 'Invalid credentials or user type'})
    return render(request, 'adlogin.html', {'next': request.GET.get('next')})
@login_required
def officer_logout(request):
    logout(request)
    return redirect('election_officer:officer_login')

@login_required
def officer_dashboard(request):
    logger.debug(f"Dashboard access by user: {request.user}, authenticated: {request.user.is_authenticated}, user type: {type(request.user)}")
    applications = ContestApplication.objects.all().order_by('-submitted_at')
    timelines = ElectionTimeline.objects.all().order_by('start_date')
    return render(request, 'addashboard.html', {
        'applications': applications,
        'timelines': timelines,
        'current_time': timezone.now()
    })

@login_required
@require_POST
@csrf_protect
def update_election_timeline(request):
    if not request.user.is_staff:
        return JsonResponse({'success': False, 'message': 'Unauthorized'}, status=403)
    try:
        data = request.POST
        start_date = data.get('start_date')
        end_date = data.get('end_date')
        if not start_date or not end_date:
            return JsonResponse({'success': False, 'message': 'Dates are required'}, status=400)
        timeline = ElectionTimeline.objects.create(
            start_date=start_date,
            end_date=end_date,
            created_by=request.user
        )
        return JsonResponse({
            'success': True,
            'message': 'Timeline updated',
            'timeline_id': timeline.id
        })
    except Exception as e:
        return JsonResponse({'success': False, 'message': str(e)}, status=500)

@login_required
@require_POST
@csrf_protect
def manage_contest_application(request):
    if not request.user.is_staff:
        return JsonResponse({'success': False, 'message': 'Unauthorized'}, status=403)
    try:
        data = request.POST
        application_id = data.get('application_id')
        action = data.get('action')
        rejection_reason = data.get('rejection_reason', '')

        application = ContestApplication.objects.get(id=application_id)
        if action == 'approve':
            application.approved = True
            application.rejected = False
            message = 'Your contest application has been approved.'
        elif action == 'reject':
            application.approved = False
            application.rejected = True
            application.rejection_reason = rejection_reason
            message = f'Your contest application has been rejected. Reason: {rejection_reason}'
        else:
            return JsonResponse({'success': False, 'message': 'Invalid action'}, status=400)

        application.save()
        UserMessage.objects.create(user=application.user, message_text=message)
        return JsonResponse({'success': True, 'message': 'Application updated'})
    except ContestApplication.DoesNotExist:
        return JsonResponse({'success': False, 'message': 'Application not found'}, status=404)
    except Exception as e:
        return JsonResponse({'success': False, 'message': str(e)}, status=500)