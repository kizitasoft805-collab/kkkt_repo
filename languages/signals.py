# accounts/signals.py
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.conf import settings
from .models import LanguageSetting

@receiver(post_save, sender=settings.AUTH_USER_MODEL)
def create_language_setting(sender, instance, created, **kwargs):
    if created:
        LanguageSetting.objects.create(user=instance, is_english=True, is_kiswahili=False)
