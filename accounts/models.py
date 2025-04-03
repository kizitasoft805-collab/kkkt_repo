from django.db import models
from django.contrib.auth.models import AbstractUser
from django.core.validators import RegexValidator
from members.models import ChurchMember  # Import ChurchMember model

class CustomUser(AbstractUser):
    """
    Custom user model that adds:
    - Phone number (must start with +255)
    - User type (admin, church member)
    - Links Church Members to system users
    - Profile picture
    - Date created (automatically set when the record is created)
    - Agreement to terms and conditions
    """

    email = models.EmailField('email address', blank=True, null=True)

    phone_validator = RegexValidator(
        regex=r'^\+255\d{9}$',
        message="Phone number must be in the format: +255XXXXXXXXX (9 digits after +255)."
    )

    phone_number = models.CharField(
        max_length=13,
        unique=True,
        validators=[phone_validator],
        help_text="Format: +255XXXXXXXXX (9 digits after +255)."
    )

    USER_TYPES = [
        ('ADMIN', 'Admin (Superuser)'),
        ('CHURCH_MEMBER', 'Church Member'),
    ]
    user_type = models.CharField(
        max_length=30,
        choices=USER_TYPES,
        default='CHURCH_MEMBER',
        help_text="Indicates the role this user will have in the system."
    )

    # Link to Church Member (Optional, Only for CHURCH_MEMBER users)
    church_member = models.OneToOneField(
        ChurchMember,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name="user_account",
        help_text="Church Member linked to this user (only required for CHURCH_MEMBER users)."
    )

    # Profile picture
    profile_picture = models.ImageField(
        upload_to='profile_pictures/',  # Directory within the MEDIA_ROOT
        blank=True,
        null=True,
        help_text="Upload a profile picture."
    )

    # Date and time when this user record was created
    date_created = models.DateTimeField(auto_now_add=True)

    # Agreement to terms and conditions
    is_agreed_to_terms_and_conditions = models.BooleanField(
        default=False,
        help_text="Indicates whether the user has agreed to the terms and conditions."
    )

    def __str__(self):
        return self.username

    def save(self, *args, **kwargs):
        """
        Custom save method to enforce:
        - Only CHURCH_MEMBER users can be linked to a Church Member.
        - ADMIN users must not have a linked Church Member.
        """
        if self.user_type == "ADMIN":
            self.church_member = None  # Ensure no church member is linked to Admins
        elif self.user_type == "CHURCH_MEMBER" and not self.church_member:
            raise ValueError("CHURCH_MEMBER users must be linked to a valid ChurchMember.")

        super().save(*args, **kwargs)
        
# accounts/models.py

from django.conf import settings
from django.db import models
from django.utils import timezone

class LoginHistory(models.Model):
    """
    Model to store login history information and last visited path.
    """
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, 
        on_delete=models.CASCADE,
        related_name='login_history'
    )
    login_time = models.DateTimeField(default=timezone.now)
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    user_agent = models.TextField(null=True, blank=True)
    last_visited_path = models.CharField(max_length=255, null=True, blank=True)

    def __str__(self):
        return f"{self.user.username} logged in at {self.login_time}"
