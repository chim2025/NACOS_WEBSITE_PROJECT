# nacos_app/middleware.py
from django.http import JsonResponse
from django.shortcuts import redirect
from django.urls import reverse

class RequirePasswordSetMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        response = self.get_response(request)
        return response

    def process_view(self, request, view_func, view_args, view_kwargs):
        # Skip if not authenticated
        if not request.user.is_authenticated:
            return None

        # Allow login, set-password, logout, static, etc.
        path = request.path
        if path.startswith(('/login/', '/set-password/', '/logout/', '/static/', '/media/', '/admin/')):
            return None

        # Allow election officer
        if hasattr(request.user, 'electionofficer'):
            return None

        # BLOCK DASHBOARD IF: is_migrated AND no usable password
        if getattr(request.user, 'is_migrated', False) and not request.user.has_usable_password():
            if request.path != reverse('nacos_app:set_password'):
                # Redirect to set-password
                if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                    return JsonResponse({
                        'success': False,
                        'redirect_url': '/set-password/',
                        'message': 'Please set your password first.'
                    }, status=403)
                return redirect('nacos_app:set_password')

        return None