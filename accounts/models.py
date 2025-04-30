import uuid
from django.db import models
from django.utils import timezone
from users.models import User

class AdminProfile(models.Model):
    """
    Extended profile information for admin users
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='admin_profile')
    department = models.CharField(max_length=100, blank=True, null=True)
    position = models.CharField(max_length=100, blank=True, null=True)
    employee_id = models.CharField(max_length=50, blank=True, null=True)
    admin_notes = models.TextField(blank=True)
    access_level = models.CharField(max_length=20, default='standard',
                                   choices=[
                                       ('limited', 'Limited'),
                                       ('standard', 'Standard'),
                                       ('full', 'Full'),
                                   ])
    last_login_ip = models.GenericIPAddressField(blank=True, null=True)
    preferences = models.JSONField(default=dict)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Admin Profile'
        verbose_name_plural = 'Admin Profiles'

    def __str__(self):
        return f"Admin Profile for {self.user.email}"

class AdminLoginHistory(models.Model):
    """
    Track admin login history
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='admin_login_history')
    login_time = models.DateTimeField(auto_now_add=True)
    ip_address = models.GenericIPAddressField(blank=True, null=True)
    user_agent = models.TextField(blank=True, null=True)
    session_id = models.CharField(max_length=100, blank=True, null=True)
    success = models.BooleanField(default=True)
    failure_reason = models.CharField(max_length=255, blank=True, null=True)

    class Meta:
        verbose_name = 'Admin Login History'
        verbose_name_plural = 'Admin Login Histories'
        ordering = ['-login_time']

    def __str__(self):
        return f"Login by {self.user.email} at {self.login_time}"
