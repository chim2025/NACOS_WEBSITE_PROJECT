from django.contrib.auth.backends import ModelBackend
from django.contrib.auth import get_user_model
from django.db.models import Q

class CustomUserBackend(ModelBackend):
    def authenticate(self, request, username=None, password=None, **kwargs):
        UserModel = get_user_model()
        try:
            # Try matching username against membership_id, email, or matric
            user = UserModel.objects.filter(
                Q(membership_id=username) |  # NACOS ID (reg)
                Q(email=username) |  # Email
                Q(matric=username)  # Matric number
            ).first()
            if user:
                if user.check_password(password):
                    return user
                elif user.is_migrated and not user.has_usable_password():
                    # Allow migrated users with unusable passwords
                    return user
            return None
        except UserModel.DoesNotExist:
            return None

