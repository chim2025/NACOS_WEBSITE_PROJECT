from django.db import models
from django.contrib.auth.models import AbstractBaseUser, BaseUserManager
from django.utils import timezone

class ElectionOfficerManager(BaseUserManager):
    def create_officer(self, username, password, **extra_fields):
        if not username:
            raise ValueError('The username must be set')
        officer = self.model(username=username, **extra_fields)
        officer.set_password(password)  # Hash the password
        officer.save(using=self._db)
        return officer

class ElectionOfficer(AbstractBaseUser):
    username = models.CharField(max_length=50, unique=True)
    is_active = models.BooleanField(default=True)
    is_staff = models.BooleanField(default=True)  # Allow admin access
    date_joined = models.DateTimeField(default=timezone.now)

    USERNAME_FIELD = 'username'
    objects = ElectionOfficerManager()

    def __str__(self):
        return self.username

    def has_perm(self, perm, obj=None):
        return self.is_active

    def has_module_perms(self, app_label):
        return self.is_active
