from django.contrib.auth.backends import ModelBackend
from election_officer.models import ElectionOfficer
from nacos_app.models import CustomUser
import logging

logger = logging.getLogger(__name__)

class CustomAuthBackend(ModelBackend):
    def authenticate(self, request, username=None, password=None, **kwargs):
        logger.debug(f"Authenticating: username={username}, password={password}")
        try:
            officer = ElectionOfficer.objects.get(username=username)
            if officer.check_password(password):
                logger.debug(f"Authenticated as ElectionOfficer: {officer}")
                return officer
        except ElectionOfficer.DoesNotExist:
            logger.debug("ElectionOfficer not found")

        user = super().authenticate(request, username=username, password=password, **kwargs)
        if user:
            logger.debug(f"Authenticated as CustomUser: {user}")
            return user
        logger.debug("Authentication failed")
        return None

    def get_user(self, user_id):
        try:
            # Prioritize ElectionOfficer for this context
            try:
                return ElectionOfficer.objects.get(pk=user_id)
            except ElectionOfficer.DoesNotExist:
                return CustomUser.objects.get(pk=user_id)
        except CustomUser.DoesNotExist:
            logger.debug(f"User with ID {user_id} not found in either model")
            return None
   