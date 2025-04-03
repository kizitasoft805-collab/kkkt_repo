# languages/models.py

from django.db import models
from django.conf import settings
from django.core.exceptions import ValidationError

class LanguageSetting(models.Model):
    """
    A model that stores a user's language preference (English/Kiswahili).
    Linked one-to-one with the user.
    """
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='language_setting'
    )
    is_english = models.BooleanField(default=True)
    is_kiswahili = models.BooleanField(default=False)

    def clean(self):
        if self.is_english and self.is_kiswahili:
            raise ValidationError("Cannot have both English and Kiswahili at the same time.")
        if not self.is_english and not self.is_kiswahili:
            raise ValidationError("At least one language must be active.")

    def save(self, *args, **kwargs):
        self.clean()
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.user.username} - {'English' if self.is_english else 'Kiswahili'}"
