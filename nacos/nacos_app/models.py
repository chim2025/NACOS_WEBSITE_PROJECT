from django.contrib.auth.models import AbstractUser
from django.db import models
from django.utils import timezone

class CustomUser(AbstractUser):
    # Identification and Membership
    membership_id = models.CharField(max_length=100, unique=True, blank=True, null=True)  # e.g., NACOS/CLU/24/100
    firebase_uid = models.CharField(max_length=128, blank=True, null=True)  # For Firebase index
    matric = models.CharField(max_length=100, unique=True, blank=True, null=True)  # Matriculation number
    email = models.EmailField(unique=True)

    # Personal Details
    is_migrated = models.BooleanField(default=False)
    level = models.CharField(max_length=10, blank=True, null=True)  # e.g., 100, 200
    course = models.CharField(max_length=100, blank=True, null=True)  # e.g., Computer Science
    clubs = models.JSONField(blank=True, null=True)  # Store clubs as JSON
    phone = models.CharField(max_length=20, blank=True, null=True)
    address = models.TextField(blank=True, null=True)
    first_name = models.TextField(blank=True, null=True)
    surname = models.TextField(blank=True, null=True)
    other_names = models.TextField(blank=True, null=True)
    lga = models.CharField(max_length=100, blank=True, null=True)
    state = models.CharField(max_length=100, blank=True, null=True)
    sex = models.CharField(max_length=10, blank=True, null=True)
    hobby = models.CharField(max_length=100, blank=True, null=True)  # Corrected from 'huby'
    denomination = models.CharField(max_length=100, blank=True, null=True)  # Corrected from 'denom'
    parent_phone = models.CharField(max_length=20, blank=True, null=True)
    mother_name = models.CharField(max_length=100, blank=True, null=True)
    room = models.CharField(max_length=20, blank=True, null=True)
    timestamp = models.DateTimeField(auto_now_add=True, blank=True, null=True)  # Changed to DateTimeField
    profile_picture = models.ImageField(upload_to='profile_pics/', blank=True, null=True, default=None)

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

class ContestApplication(models.Model):
    POSITION_CHOICES = [
        ('president', 'President'),
        ('vice_president', 'Vice President'),
        ('secretary', 'Secretary'),
        ('treasurer', 'Treasurer'),
        ('director1', 'Assistant Secretary'),
        ('director2', 'Assistant Treasurer'),
        ('director3', 'Director of Research and Innovation'),
        ('director4', 'Director of Sports'),
        ('director5', 'Director of Socials'),
        ('director6', 'Director of Chaplaincy'),
        ('director7', 'Director of Welfare'),
        ('director8', 'Director of Public Relations'),
        ('director9', 'Director of ICT'),
    ]

    user = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name='contest_applications')
    position = models.CharField(max_length=50, choices=POSITION_CHOICES)
    manifesto = models.TextField(max_length=500, blank=True, null=True)
    statement_of_result = models.FileField(upload_to='contest_results/', blank=True, null=True)
    account_statement = models.FileField(upload_to='contest_accounts/', blank=True, null=True)
    submitted_at = models.DateTimeField(default=timezone.now)
    approved = models.BooleanField(default=False)
    rejected = models.BooleanField(default=False)
    rejection_reason = models.TextField(blank=True, null=True)

    def __str__(self):
        return f"{self.user.username} - {self.position}"

# nacos_app/models.py
from django.contrib.auth import get_user_model
from election_officer.models import ElectionOfficer  # ← Import

class ElectionTimeline(models.Model):
    start_date = models.DateTimeField()
    end_date = models.DateTimeField()
    created_by = models.ForeignKey(
        'election_officer.ElectionOfficer',
        on_delete=models.SET_NULL,
        null=True,
        related_name='election_timelines'
    )
    created_at = models.DateTimeField(auto_now_add=True)  # ← NEW

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"Election: {self.start_date} → {self.end_date}"



class ElectionPosition(models.Model):
    name = models.CharField(max_length=100, unique=True)
    description = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['name']
        verbose_name = "Election Position"
        verbose_name_plural = "Election Positions"

    def __str__(self):
        return self.name


class ContestApplication(models.Model):
    user = models.ForeignKey(CustomUser, on_delete=models.CASCADE)
    position = models.ForeignKey(ElectionPosition, on_delete=models.CASCADE)
    manifesto = models.TextField(max_length=200)
    statement_of_result = models.FileField(upload_to='contest/results/')
    account_statement = models.FileField(upload_to='contest/accounts/')
    submitted_at = models.DateTimeField(auto_now_add=True)
    approved = models.BooleanField(default=False)
    rejected = models.BooleanField(default=False)

    def __str__(self):
        return f"{self.user} - {self.position}"


class UserMessage(models.Model):
    user = models.ForeignKey(CustomUser, on_delete=models.CASCADE)
    message_text = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    is_read = models.BooleanField(default=False)

    def __str__(self):
        return f"Message for {self.user}: {self.message_text[:50]}"
    

from django.core.exceptions import ValidationError
class Vote(models.Model):
    user = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name='votes')
    candidate = models.ForeignKey('ContestApplication', on_delete=models.CASCADE)
    position = models.ForeignKey('ElectionPosition', on_delete=models.CASCADE)
    election = models.ForeignKey('ElectionTimeline', on_delete=models.CASCADE)
    voted_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('user', 'election', 'position')  
        indexes = [
            models.Index(fields=['user', 'election']),
            models.Index(fields=['candidate']),
            models.Index(fields=['election', 'position']),
        ]
        ordering = ['-voted_at']
        verbose_name = "Vote"
        verbose_name_plural = "Votes"

    def clean(self):
        """Ensure vote is within election time"""
        if not (self.election.start_date <= timezone.now() <= self.election.end_date):
            raise ValidationError("Voting is not allowed at this time.")

    def __str__(self):
        return f"{self.user} → {self.candidate.user} ({self.position.name})"
