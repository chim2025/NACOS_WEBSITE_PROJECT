import json
from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login, logout
from django.http import JsonResponse
from django.contrib.auth.decorators import login_required
from django.views.decorators.csrf import csrf_protect, csrf_exempt, csrf_protect 
from django.views.decorators.http import require_POST
from django.utils import timezone
from nacos_app.models import ContestApplication, ElectionTimeline, UserMessage, Vote
from election_officer.models import ElectionOfficer
from nacos_app.models import CustomUser, ContestApplication, ElectionTimeline
from django.views.decorators.http import require_http_methods
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
    logger.debug(f"Dashboard access by user: {request.user}, authenticated: {request.user.is_authenticated}")
    if not isinstance(request.user, ElectionOfficer):
        return redirect('election_officer:officer_login')

    # === Applications ===
    applications = ContestApplication.objects.all().order_by('-submitted_at')
    total_apps = applications.count()
    pending = applications.filter(approved=False, rejected=False).count()
    approved = applications.filter(approved=True).count()
    rejected = applications.filter(rejected=True).count()

    # === Students ===
    # === Students (users with level and matric number) ===
    students = CustomUser.objects.exclude(level__isnull=True).exclude(level='').exclude(matric__isnull=True).exclude(matric='')
    total_students = students.count()
    level_counts = {
        '100': students.filter(level='100').count(),
        '200': students.filter(level='200').count(),
        '300': students.filter(level='300').count(),
        '400': students.filter(level='400').count(),
        '500': students.filter(level='500').count(),
    }

    # === Timelines ===
    timelines = ElectionTimeline.objects.all().order_by('start_date')
    latest_timeline = ElectionTimeline.objects.order_by('-created_at').first()

    # === Context ===
    context = {
        'applications': applications,
        'timelines': timelines,
        'current_time': timezone.now(),
        'stats': {
            'total_students': total_students,
            'level_counts': level_counts,
            'total_apps': total_apps,
            'pending': pending,
            'approved': approved,
            'rejected': rejected,
        },
        'latest_timeline': latest_timeline,  # for greeting card
    }

    return render(request, 'addashboard.html', context)

# views.py
from django.utils import timezone
from datetime import datetime
import logging
logger = logging.getLogger(__name__)

@login_required
@require_POST
@csrf_protect
def update_election_timeline(request):
    if not request.user.is_staff:
        return JsonResponse({'success': False, 'message': 'Unauthorized'}, status=403)

    try:
        start_str = request.POST.get('start_date')
        end_str = request.POST.get('end_date')

        if not start_str or not end_str:
            return JsonResponse({'success': False, 'message': 'Both dates are required.'}, status=400)

        # Parse as naive first
        naive_start = datetime.fromisoformat(start_str.replace('T', ' '))
        naive_end = datetime.fromisoformat(end_str.replace('T', ' '))

        # Convert to aware using Django's timezone
        local_tz = timezone.get_current_timezone()
        start = timezone.make_aware(naive_start, local_tz)
        end = timezone.make_aware(naive_end, local_tz)
        now = timezone.now()  # ← already aware

        # Validation
        if start >= end:
            return JsonResponse({'success': False, 'message': 'End time must be after start time.'}, status=400)
        if end <= now:
            return JsonResponse({'success': False, 'message': 'End time cannot be in the past.'}, status=400)
        if start <= now:
            return JsonResponse({'success': False, 'message': 'Start time cannot be in the past.'}, status=400)

        # Save
        timeline = ElectionTimeline.objects.create(
            start_date=start,
            end_date=end,
            created_by=request.user
        )

        return JsonResponse({
            'success': True,
            'message': 'Timeline saved!',
            'timeline': {
                'start': start.strftime('%b %d, %Y %I:%M %p'),
                'end': end.strftime('%b %d, %Y %I:%M %p'),
                'created': timeline.created_at.strftime('%b %d, %I:%M %p')
            }
        })

    except ValueError as e:
        logger.error(f"Date parse error: {e}")
        return JsonResponse({'success': False, 'message': 'Invalid date format.'}, status=400)
    except Exception as e:
        logger.error(f"Timeline error: {e}")
        return JsonResponse({'success': False, 'message': 'Server error.'}, status=500)
from django.utils import timezone


@login_required
def get_latest_timeline(request):
    # NEW: order by created_at DESC + id DESC → stable, always the newest insert
    latest = ElectionTimeline.objects.order_by('-created_at', '-id').first()
    if latest and latest.start_date and latest.end_date:
        local_tz = timezone.get_current_timezone()
        local_start = latest.start_date.astimezone(local_tz)
        local_end   = latest.end_date.astimezone(local_tz)

        return JsonResponse({
            'success': True,
            'latest': {
                'start_date': local_start.replace(tzinfo=None).isoformat(),
                'end_date'  : local_end.replace(tzinfo=None).isoformat(),
            }
        })
    return JsonResponse({'success': False, 'message': 'No timeline set'})

@login_required
@require_POST
@csrf_protect  # Ensures CSRF check, but returns JSON on failure
def delete_timeline(request, pk):
    try:
        if not request.user.is_staff:
            return JsonResponse({'success': False, 'message': 'Unauthorized: Staff only'}, status=403)

        # Log the request for debug
        logger.info(f"Delete attempt for timeline {pk} by {request.user.username}")

        timeline = ElectionTimeline.objects.get(pk=pk)
        timeline.delete()
        
        logger.info(f"Timeline {pk} deleted by {request.user.username}")
        return JsonResponse({'success': True, 'message': 'Timeline deleted successfully'})

    except ElectionTimeline.DoesNotExist:
        logger.warning(f"Timeline {pk} not found")
        return JsonResponse({'success': False, 'message': 'Timeline not found'}, status=404)
    except Exception as e:
        logger.error(f"Delete timeline {pk} error: {e}")
        return JsonResponse({'success': False, 'message': 'Server error occurred'}, status=500)
    
    
@login_required
@require_POST
@csrf_protect
def manage_contest_application(request):
    if not isinstance(request.user, ElectionOfficer):
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
@login_required
def officer_notifications(request):
    """Return unread messages for the logged-in officer."""
    msgs = UserMessage.objects.filter(user=request.user, read=False).order_by('-created_at')
    data = [{
        'id': m.id,
        'text': m.message_text,
        'time': m.created_at.strftime('%b %d %H:%M')
    } for m in msgs]
    return JsonResponse({'notifications': data})

from nacos_app.models import ElectionPosition

import re
from django.core.exceptions import ValidationError

@login_required
@require_POST
@csrf_protect
def create_position(request):
    raw_name = request.POST.get('name', '').strip()
    description = request.POST.get('description', '').strip()

    if not raw_name:
        return JsonResponse({'success': False, 'message': 'Position name is required.'})

    if len(raw_name) > 100:
        return JsonResponse({'success': False, 'message': 'Name too long (max 100 chars).'})

    # === NORMALIZE NAME FOR COMPARISON ===
    # 1. Lowercase
    # 2. Replace hyphens, underscores, spaces with single space
    # 3. Strip and collapse multiple spaces
    normalized = re.sub(r'[-_\s]+', ' ', raw_name.lower()).strip()
    if not normalized:
        return JsonResponse({'success': False, 'message': 'Invalid position name.'})

    # === CHECK IF SIMILAR POSITION EXISTS ===
    # Search across all existing positions
    existing = ElectionPosition.objects.filter(
        name__regex=r'(?i)^' + re.escape(normalized.replace(' ', '[-_ ]*')) + r'$'
    ).first()

    if existing:
        return JsonResponse({
            'success': False,
            'message': f'Position already exists: "{existing.name}"'
        })

    # === SAVE CANONICAL NAME ===
    # Use original casing, but clean up hyphens/spaces
    clean_name = re.sub(r'\s+', ' ', raw_name).strip()
    clean_name = re.sub(r'[-_]+', '-', clean_name)  # optional: standardize to hyphen

    try:
        position = ElectionPosition.objects.create(
            name=clean_name,
            description=description
        )
    except ValidationError as e:
        return JsonResponse({'success': False, 'message': str(e)})

    return JsonResponse({
        'success': True,
        'message': 'Position created!',
        'position': {
            'id': position.id,
            'name': position.name,
            'description': position.description or 'No description'
        }
    })
@login_required
def get_positions(request):
    positions = ElectionPosition.objects.all()
    data = [{
        'id': p.id,
        'name': p.name,
        'description': p.description or 'No description'
    } for p in positions]
    return JsonResponse({'positions': data})



@login_required
@require_POST
@csrf_protect
def delete_position(request, pk):
    if not request.user.is_staff:
        return JsonResponse({'success': False, 'message': 'Unauthorized'}, status=403)

    try:
        position = ElectionPosition.objects.get(pk=pk)
        position.delete()
        return JsonResponse({'success': True, 'message': 'Position deleted'})
    except ElectionPosition.DoesNotExist:
        return JsonResponse({'success': False, 'message': 'Position not found'}, status=404)

# election_officer/views.py
from django.db.models import Count
from django.utils import timezone

@login_required
def election_live(request):
    # Get most recent election (active OR ended)
    election = ElectionTimeline.objects.filter(
        start_date__lte=timezone.now()
    ).order_by('-end_date').first()

    if not election:
        return JsonResponse({'live': []})

    positions = ElectionPosition.objects.all()
    data = []

    for pos in positions:
        # Get all approved candidates for this position
        applications = ContestApplication.objects.filter(
            position=pos, approved=True
        ).select_related('user')

        # Count votes for each candidate
        vote_counts = Vote.objects.filter(
            position=pos, election=election
        ).values('candidate').annotate(votes=Count('candidate'))

        # Build candidate list with vote count
        candidates = []
        for app in applications:
            vote_data = next((v for v in vote_counts if v['candidate'] == app.id), None)
            votes = vote_data['votes'] if vote_data else 0
            candidates.append({
                'name': f"{app.user.surname} {app.user.first_name}".strip() or app.user.username,
                'votes': votes,
                'photo': app.user.profile_picture.url if app.user.profile_picture else None,
                'votes': votes,
                'matric': app.user.matric or app.user.membership_id or '—',
                'batch': app.user.level or ''  
            })

        data.append({
            'position': pos.name,
            'candidates': candidates
        })

    return JsonResponse({
        'live': data,
        'election_status': 'ended' if election.end_date < timezone.now() else 'live'
    })
# election_officer/views.py
@login_required
def get_applications_api(request):
    if not isinstance(request.user, ElectionOfficer):
        return JsonResponse({'error': 'Unauthorized'}, status=403)

    apps = ContestApplication.objects.select_related('user', 'position').all()
    data = []
    for app in apps:
        profile_pic = app.user.profile_picture.url if app.user.profile_picture else None
        if profile_pic:
            profile_pic = request.build_absolute_uri(profile_pic)

        data.append({
            'id': app.id,
            'student': app.user.get_full_name() or app.user.username,
            'user_email': app.user.email,
            'position': app.position.name,
            'submitted_at': app.submitted_at.strftime("%b %d, %I:%M %p"),
            'result_file': request.build_absolute_uri(app.statement_of_result.url) if app.statement_of_result else '',
            'account_file': request.build_absolute_uri(app.account_statement.url) if app.account_statement else '',
            'profile_pic': profile_pic,
            'approved': app.approved,
            'rejected': app.rejected,
        })
    return JsonResponse({'applications': data})
from nacos_app.models import ContestApplication, UserMessage

@login_required
@require_http_methods(["POST"])
def approve_application(request, app_id):
    if not isinstance(request.user, ElectionOfficer):
        return JsonResponse({'success': False, 'message': 'Unauthorized'}, status=403)

    try:
        app = ContestApplication.objects.get(id=app_id)
        app.approved = True
        app.rejected = False
        app.save()

        UserMessage.objects.create(
            user=app.user,
            message_text=f'Your application for {app.position.name} has been APPROVED!'
        )
        return JsonResponse({'success': True})
    except ContestApplication.DoesNotExist:
        return JsonResponse({'success': False, 'message': 'Application not found'}, status=404)
    except Exception as e:
        return JsonResponse({'success': False, 'message': str(e)}, status=500)


@login_required
@require_http_methods(["POST"])
def reject_application(request, app_id):
    if not isinstance(request.user, ElectionOfficer):
        return JsonResponse({'success': False, 'message': 'Unauthorized'}, status=403)

    try:
        app = ContestApplication.objects.get(id=app_id)
        app.rejected = True
        app.approved = False
        app.save()

        UserMessage.objects.create(
            user=app.user,
            message_text=f'Your application for {app.position.name} has been REJECTED.'
        )
        return JsonResponse({'success': True})
    except ContestApplication.DoesNotExist:
        return JsonResponse({'success': False, 'message': 'Application not found'}, status=404)
    except Exception as e:
        return JsonResponse({'success': False, 'message': str(e)}, status=500)
# views.py
@login_required
@require_POST
@csrf_exempt   # we will send CSRF token from JS
def delete_timeline(request, pk):
    if not request.user.is_staff:
        return JsonResponse({'success': False, 'message': 'Unauthorized'}, status=403)

    try:
        timeline = ElectionTimeline.objects.get(pk=pk)
        timeline.delete()
        return JsonResponse({'success': True, 'message': 'Deleted'})
    except ElectionTimeline.DoesNotExist:
        return JsonResponse({'success': False, 'message': 'Not found'}, status=404)
    except Exception as e:
        logger.error(f"Delete error: {e}")
        return JsonResponse({'success': False, 'message': 'Server error'}, status=500)
from django.conf import settings

@login_required
def get_students_api(request):
    students = CustomUser.objects.filter(
        is_migrated=True  # adjust if needed
    ).select_related().values(
        'id', 'first_name', 'surname', 'matric', 'course', 'level', 'is_active', 'profile_picture'
    )

    data = []
    for s in students:
        full_name = f"{s['first_name'] or ''} {s['surname'] or ''}".strip() or s['matric'] or 'Unknown'
        photo_url = None
        if s['profile_picture']:
            photo_url = request.build_absolute_uri(s['profile_picture'].url)
        
        data.append({
            'id': s['id'],
            'name': full_name,
            'matric': s['matric'] or 'N/A',
            'dept': s['course'] or 'N/A',
            'level': s['level'] or 'N/A',
            'status': 'Active' if s['is_active'] else 'Inactive',
            'photo': photo_url
        })

    return JsonResponse({'students': data})

'''
@login_required
def get_election_options(request):
    levels = CustomUser.objects.exclude(level__isnull=True).exclude(level='').values('level').annotate(count=Count('level')).order_by('level')
    levels_list = [{'id': item['level'], 'name': f"{item['level']} Level"} for item in levels]

    depts = CustomUser.objects.exclude(department__isnull=True).exclude(department='').values('department').annotate(count=Count('department')).order_by('department')
    depts_list = [{'id': item['department'], 'name': item['department']} for item in depts]

    return JsonResponse({
        'levels': levels_list,
        'departments': depts_list,
    })

@login_required
def get_current_settings(request):
    election = ElectionTimeline.objects.order_by('-end_date').first()
    if not election:
        return JsonResponse({})

    return JsonResponse({
        'start_date': election.start_date.strftime('%Y-%m-%dT%H:%M') if election.start_date else '',
        'end_date': election.end_date.strftime('%Y-%m-%dT%H:%M') if election.end_date else '',
        'voter_levels': election.voter_levels or [],
        'voter_departments': election.voter_departments or [],
        'candidate_levels': election.candidate_levels or [],
        'candidate_departments': election.candidate_departments or [],
        'allow_all_voters': election.allow_all_voters,
        'allow_all_candidates': election.allow_all_candidates,
        'show_live_results': election.show_live_results,
    })

@csrf_exempt
@login_required
def save_election_settings(request):
    if request.method != 'POST':
        return JsonResponse({'error': 'POST required'})

    import json
    data = json.loads(request.body)
    election = ElectionTimeline.objects.order_by('-end_date').first()

    if not election:
        return JsonResponse({'error': 'No election found'})

    election.start_date = data.get('start_date')
    election.end_date = data.get('end_date')
    election.voter_levels = data.get('voter_levels', [])
    election.voter_departments = data.get('voter_departments', [])
    election.candidate_levels = data.get('candidate_levels', [])
    election.candidate_departments = data.get('candidate_departments', [])
    election.allow_all_voters = data.get('allow_all_voters', False)
    election.allow_all_candidates = data.get('allow_all_candidates', False)
    election.show_live_results = data.get('show_live_results', True)
    election.save()

    return JsonResponse({'success': True})
'''