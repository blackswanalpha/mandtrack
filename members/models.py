import uuid
from django.db import models
from django.conf import settings
# Use string reference to avoid circular imports

class Member(models.Model):
    """
    Model for members who can access questionnaires with access codes
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    member_number = models.CharField(max_length=50, unique=True)
    name = models.CharField(max_length=255, blank=True, null=True)
    email = models.EmailField(blank=True, null=True)
    phone = models.CharField(max_length=20, blank=True, null=True)
    organization = models.ForeignKey('groups.Organization', on_delete=models.CASCADE, related_name='org_members')
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Member'
        verbose_name_plural = 'Members'
        ordering = ['member_number']

    def __str__(self):
        return f"{self.member_number} - {self.name or 'Unnamed Member'}"


class MemberAccess(models.Model):
    """
    Model for tracking member access to questionnaires
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    member = models.ForeignKey(Member, on_delete=models.CASCADE, related_name='accesses')
    questionnaire = models.ForeignKey('surveys.SurveysQuestionnaire', on_delete=models.CASCADE, related_name='member_accesses')
    access_code = models.CharField(max_length=20)
    is_used = models.BooleanField(default=False)
    used_at = models.DateTimeField(blank=True, null=True)
    expires_at = models.DateTimeField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'Member Access'
        verbose_name_plural = 'Member Accesses'
        unique_together = ['member', 'questionnaire', 'access_code']
        ordering = ['-created_at']

    def __str__(self):
        return f"Access for {self.member} to {self.questionnaire.title}"
