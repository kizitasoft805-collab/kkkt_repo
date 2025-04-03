from django.db import models
from django.utils.timezone import now
from members.models import ChurchMember

class Notification(models.Model):
    """
    Model to store notifications sent to Church Members.
    """

    # Title of the Notification
    title = models.CharField(
        max_length=255,
        help_text="Title or subject of the notification."
    )

    # Message Body
    message = models.TextField(
        help_text="Detailed message content of the notification."
    )

    # Recipient: Church Member (Now REQUIRED)
    church_member = models.ForeignKey(
        ChurchMember, 
        on_delete=models.CASCADE,  # Ensure notifications are deleted if a member is removed
        null=False, blank=False,   # Make it required (Cannot be NULL)
        related_name="notifications",
        help_text="Church member receiving the notification. Required field."
    )

    # Read Status
    is_read = models.BooleanField(
        default=False,
        help_text="Has the notification been read?"
    )

    # Date Created
    created_at = models.DateTimeField(
        default=now,
        editable=False,
        help_text="Timestamp of when the notification was created."
    )

    def __str__(self):
        return f"To: {self.church_member.full_name} | {self.title} - {'Read' if self.is_read else 'Unread'}"

    class Meta:
        ordering = ['-created_at']  # Show latest notifications first
        verbose_name = "Notification"
        verbose_name_plural = "Notifications"
