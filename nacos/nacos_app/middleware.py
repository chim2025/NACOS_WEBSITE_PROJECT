
from django.conf import settings
from django.http import JsonResponse
from django.utils import timezone
from .models import ElectionTimeline, Vote, ContestApplication
import json

import logging
import traceback
from django.utils.deprecation import MiddlewareMixin

logger = logging.getLogger(__name__)
class ErrorHandlingMiddleware(MiddlewareMixin):
    def process_exception(self, request, exception):
        # Only handle API endpoints
        if not request.path.startswith('/api/'):
            return None

        # Log full error
        logger.error(
            f"API Error: {request.path}\n"
            f"User: {request.user}\n"
            f"Exception: {type(exception).__name__}\n"
            f"Message: {str(exception)}\n"
            f"Traceback:\n{traceback.format_exc()}"
        )

        # Return clean JSON
        return JsonResponse({
            'error': 'Internal server error',
            'detail': str(exception) if settings.DEBUG else None
        }, status=500)

class VoteValidationMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        return self.get_response(request)

    def process_view(self, request, view_func, view_args, view_kwargs):
        # Only apply to submit_vote POST
        if not (request.path.endswith('/api/submit-vote/') and request.method == 'POST'):
            return None

        try:
            # Parse JSON body
            if not request.body:
                return JsonResponse({'error': 'Empty request body'}, status=400)
            
            data = json.loads(request.body)
            votes = data.get('votes', {})

            if not isinstance(votes, dict):
                return JsonResponse({'error': 'Invalid votes format'}, status=400)

            # 1. Check active election
            election = ElectionTimeline.objects.filter(
                start_date__lte=timezone.now(),
                end_date__gte=timezone.now()
            ).first()

            if not election:
                return JsonResponse({'error': 'No active election'}, status=400)

            # 2. Prevent double voting
            if Vote.objects.filter(user=request.user, election=election).exists():
                return JsonResponse({'error': 'You have already voted in this election'}, status=403)

            # 3. Validate each candidate
            for position_id, candidate_id in votes.items():
                if not ContestApplication.objects.filter(
                    id=candidate_id,
                    position_id=position_id,
                    approved=True
                ).exists():
                    return JsonResponse({
                        'error': f'Invalid or unapproved candidate for position ID {position_id}'
                    }, status=400)

            # Attach validated data
            request.validated_votes = votes
            request.active_election = election

        except json.JSONDecodeError:
            return JsonResponse({'error': 'Invalid JSON'}, status=400)
        except Exception as e:
            return JsonResponse({'error': 'Validation failed'}, status=400)

        return None