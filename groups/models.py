from django.db import models
from django.conf import settings
from django.utils.text import slugify

class Organization(models.Model):
    """
    Model for organizations
    """
    TYPE_CHOICES = [
        ('healthcare', 'Healthcare'),
        ('education', 'Education'),
        ('research', 'Research'),
        ('government', 'Government'),
        ('nonprofit', 'Non-Profit'),
        ('corporate', 'Corporate'),
        ('other', 'Other'),
    ]

    name = models.CharField(max_length=255)
    slug = models.SlugField(max_length=255, unique=True, blank=True)
    description = models.TextField(blank=True)
    type = models.CharField(max_length=20, choices=TYPE_CHOICES, default='healthcare')
    website = models.URLField(blank=True, null=True)
    email = models.EmailField(blank=True, null=True)
    phone = models.CharField(max_length=20, blank=True, null=True)
    address = models.TextField(blank=True, null=True)
    logo = models.ImageField(upload_to='organization_logos/', blank=True, null=True)
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, related_name='created_organizations')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['name']
        verbose_name = 'Organization'
        verbose_name_plural = 'Organizations'

    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
        # Generate slug if not provided
        if not self.slug:
            self.slug = slugify(self.name)

            # Ensure slug is unique
            original_slug = self.slug
            counter = 1
            while Organization.objects.filter(slug=self.slug).exists():
                self.slug = f"{original_slug}-{counter}"
                counter += 1

        super().save(*args, **kwargs)

    def get_member_count(self):
        return self.members.count()

    def get_survey_count(self):
        return self.surveys.count()


class OrganizationMember(models.Model):
    """
    Model for organization members
    """
    ROLE_CHOICES = [
        ('admin', 'Administrator'),
        ('manager', 'Manager'),
        ('provider', 'Healthcare Provider'),
        ('staff', 'Staff'),
        ('researcher', 'Researcher'),
        ('viewer', 'Viewer'),
    ]

    organization = models.ForeignKey(Organization, on_delete=models.CASCADE, related_name='members')
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='organizations')
    role = models.CharField(max_length=20, choices=ROLE_CHOICES, default='staff')
    title = models.CharField(max_length=255, blank=True, null=True)
    department = models.CharField(max_length=255, blank=True, null=True)
    is_active = models.BooleanField(default=True)
    joined_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['organization', 'user__last_name', 'user__first_name']
        verbose_name = 'Organization Member'
        verbose_name_plural = 'Organization Members'
        unique_together = ['organization', 'user']

    def __str__(self):
        return f"{self.user} ({self.get_role_display()}) in {self.organization}"

    def is_admin(self):
        return self.role == 'admin'

    def can_manage_surveys(self):
        return self.role in ['admin', 'manager', 'provider']

    def can_view_responses(self):
        return self.role in ['admin', 'manager', 'provider', 'researcher']
