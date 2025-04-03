from django.db import models
from django.utils.timezone import now
from members.models import ChurchMember

class SentSMS(models.Model):
    """
    Stores details of SMS messages sent via Beem.
    """
    recipient = models.ForeignKey(ChurchMember, on_delete=models.CASCADE, related_name="sent_sms")
    phone_number = models.CharField(max_length=15, help_text="Recipient's phone number.")
    message = models.TextField(help_text="Message content.")
    request_id = models.CharField(max_length=50, help_text="Beem API request ID.")
    status = models.CharField(max_length=20, default="PENDING", help_text="SMS delivery status.")
    sent_at = models.DateTimeField(default=now, help_text="Time when the SMS was sent.")

    def __str__(self):
        return f"{self.recipient.full_name} - {self.status}"
