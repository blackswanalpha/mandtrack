from django.db import models
from django.contrib.auth import get_user_model
from django.contrib.contenttypes.fields import GenericForeignKey
from django.contrib.contenttypes.models import ContentType

User = get_user_model()

class Notification(models.Model):
    """
    Model for storing user notifications
    """
    NOTIFICATION_TYPES = (
        ('info', 'Information'),
        ('success', 'Success'),
        ('warning', 'Warning'),
        ('error', 'Error'),
    )

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='notifications')
    title = models.CharField(max_length=255)
    message = models.TextField()
    notification_type = models.CharField(max_length=20, choices=NOTIFICATION_TYPES, default='info')
    is_read = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    # Optional link to related object
    content_type = models.ForeignKey(ContentType, on_delete=models.CASCADE, null=True, blank=True)
    object_id = models.PositiveIntegerField(null=True, blank=True)
    content_object = GenericForeignKey('content_type', 'object_id')

    # URL to redirect to when notification is clicked
    url = models.CharField(max_length=255, blank=True, null=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.title} - {self.user.email}"

    def mark_as_read(self):
        """Mark notification as read"""
        self.is_read = True
        self.save()

    @classmethod
    def create_notification(cls, user, title, message, notification_type='info', related_object=None, url=None):
        """
        Create a new notification

        Args:
            user: User to notify
            title: Notification title
            message: Notification message
            notification_type: Type of notification (info, success, warning, error)
            related_object: Optional related object
            url: Optional URL to redirect to

        Returns:
            Notification object
        """
        notification = cls(
            user=user,
            title=title,
            message=message,
            notification_type=notification_type,
            url=url
        )

        if related_object:
            notification.content_object = related_object

        notification.save()
        return notification
