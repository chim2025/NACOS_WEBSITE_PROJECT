from django.contrib.auth.models import AbstractUser
from django.db import models

class CustomUser(AbstractUser):
    membership_id = models.CharField(max_length=50, unique=True, blank=True, null=True)  # For reg, e.g., NACOS/CLU/24/100
    firebase_uid = models.CharField(max_length=128, blank=True, null=True)  # For Firebase index
    is_migrated = models.BooleanField(default=False)
    matric = models.CharField(max_length=50, unique=True, blank=True, null=True)  # Matriculation number
    level = models.CharField(max_length=10, blank=True, null=True)  # e.g., 100, 200
    course = models.CharField(max_length=100, blank=True, null=True)  # e.g., Computer Science
    clubs = models.JSONField(blank=True, null=True)  # Store clubs as JSON
    phone = models.CharField(max_length=20, blank=True, null=True)
    address = models.TextField(blank=True, null=True)
    first_name= models.TextField(blank=True, null=True)
    surname=models.TextField(blank=True, null=True)
    other_names= models.TextField(blank=True, null=True)
    lga = models.CharField(max_length=100, blank=True, null=True)
    state = models.CharField(max_length=100, blank=True, null=True)
    sex = models.CharField(max_length=10, blank=True, null=True)
    hobby = models.CharField(max_length=100, blank=True, null=True)  # huby in JSON
    denomination = models.CharField(max_length=100, blank=True, null=True)  # denom
    parent_phone = models.CharField(max_length=20, blank=True, null=True)
    mother_name = models.CharField(max_length=100, blank=True, null=True)
    room = models.CharField(max_length=20, blank=True, null=True)
    timestamp=models.CharField(max_length=200, blank=True, null=True)
    profile_picture = models.ImageField(upload_to='profile_pics/', blank=True, null=True, default=None)  # Profile picture field

    # Override groups and user_permissions to avoid reverse accessor conflicts
    groups = models.ManyToManyField(
        'auth.Group',
        related_name='customuser_set',  # Unique related_name
        blank=True,
        help_text='The groups this user belongs to.',
        verbose_name='groups',
    )
    user_permissions = models.ManyToManyField(
        'auth.Permission',
        related_name='customuser_set',  # Unique related_name
        blank=True,
        help_text='Specific permissions for this user.',
        verbose_name='user permissions',
    )

    def __str__(self):
        return self.username