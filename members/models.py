import random
import string
from django.db import models
from django.core.validators import RegexValidator
from django.utils.timezone import now
from django.core.exceptions import ValidationError
from settings.models import Cell


class ChurchMember(models.Model):
    """
    Model to represent a church member.
    """

    # Validators
    phone_validator = RegexValidator(
        regex=r'^255\d{9}$',
        message="Phone number must be in the format: 255XXXXXXXXX (9 digits after 255)."
    )
    email_validator = RegexValidator(
        regex=r'^[a-zA-Z0-9._%+-]+@gmail\.com$',
        message="Email must be a valid Gmail address and end with '@gmail.com'."
    )

    # Unique Member ID
    member_id = models.CharField(
        max_length=20,
        unique=True,
        blank=True,
        null=True,
        help_text="Unique ID consisting of a highly randomized mix of 10 letters and 10 numbers."
    )

    # Status Field
    STATUS_CHOICES = [
        ('Active', 'Active'),
        ('Inactive', 'Inactive'),
        ('Pending', 'Pending'),
    ]
    status = models.CharField(
        max_length=10,
        choices=STATUS_CHOICES,
        default='Pending',
        help_text="Indicates whether the church member is active, inactive, or pending."
    )

    # Date Created
    date_created = models.DateTimeField(
        default=now,
        editable=False,
        help_text="Date and time when the member was created."
    )

    # Basic Information
    full_name = models.CharField(max_length=255, help_text="Full name of the church member.")
    date_of_birth = models.DateField(help_text="Date of birth.")
    gender = models.CharField(
        max_length=10,
        choices=[('Male', 'Male'), ('Female', 'Female')],
        help_text="Gender of the church member."
    )
    phone_number = models.CharField(
        max_length=12,
        unique=True,
        validators=[phone_validator],
        help_text="Phone number in the format: 255XXXXXXXXX."
    )
    email = models.EmailField(
        blank=True,
        null=True,
        validators=[email_validator],
        help_text="Email address (must end with '@gmail.com')."
    )
    address = models.TextField(help_text="Full address of the church member.")

    # Cell
    cell = models.ForeignKey(
        Cell,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="members",
        help_text="The cell this church member belongs to."
    )

    # Baptism Fields
    is_baptised = models.BooleanField(default=False, help_text="Has the member been baptized?")
    date_of_baptism = models.DateField(blank=True, null=True, help_text="Date of baptism (if baptized).")
    baptism_certificate = models.FileField(
        upload_to='baptism_certificates/',
        blank=True,
        null=True,
        help_text="Upload baptism certificate or document."
    )

    # Confirmation Fields
    date_confirmed = models.DateField(blank=True, null=True, help_text="Date of confirmation (if confirmed).")
    confirmation_certificate = models.FileField(
        upload_to='confirmation_certificates/',
        blank=True,
        null=True,
        help_text="Upload Confirmation certificate or document."
    )
    is_confirmed = models.BooleanField(default=False, help_text="Has the member been confirmed?")

    # Leadership Status
    is_this_church_member_a_leader = models.BooleanField(
        default=False,
        help_text="Indicates whether this church member is a leader."
    )

    # Marital Status
    marital_status = models.CharField(
        max_length=20,
        choices=[
            ('Single', 'Single'),
            ('Married', 'Married'),
            ('Divorced', 'Divorced'),
            ('Widowed', 'Widowed'),
        ],
        help_text="Marital status of the church member."
    )
    date_of_marriage = models.DateField(blank=True, null=True, help_text="Date of marriage (if married).")

    # Emergency Contact
    emergency_contact_name = models.CharField(
        max_length=255,
        help_text="Name of the person to contact during an emergency."
    )
    emergency_contact_phone = models.CharField(
        max_length=12,
        validators=[phone_validator],
        help_text="Phone number of the emergency contact (format: 255XXXXXXXXX)."
    )

    # Other Details
    passport = models.ImageField(
        upload_to='church_member_passports/',
        blank=True,
        null=True,
        help_text="Upload the passport photo of the member."
    )

    def __str__(self):
        return f"{self.full_name} ({self.phone_number}) - {self.status} - Confirmed: {self.is_confirmed} - Leader: {self.is_this_church_member_a_leader}"

    def generate_unique_member_id(self):
        """
        Generates a highly randomized unique 20-character member ID.
        """
        while True:
            characters = list(
                ''.join(random.choices(string.ascii_uppercase, k=10)) +
                ''.join(random.choices(string.digits, k=10))
            )
            random.shuffle(characters)
            member_id = ''.join(characters)

            if not ChurchMember.objects.filter(member_id=member_id).exists():
                return member_id

    def clean(self):
        super().clean()

    def save(self, *args, **kwargs):
        """
        Overrides save to:
        - Generate member_id if not set.
        - Send SMS on status change to Active with member_id instructions.
        """
        # Store original status for comparison
        original_status = None
        if self.pk:
            original_status = ChurchMember.objects.get(pk=self.pk).status

        # Generate member_id if not set
        if not self.member_id:
            self.member_id = self.generate_unique_member_id()

        # Run validations
        self.full_clean()

        # Save the instance
        super().save(*args, **kwargs)

        # Send SMS if status changed to Active
        if original_status != 'Active' and self.status == 'Active':
            from sms.utils import send_sms  # Import here to avoid circular import
            approval_message = (
                f"Hongera {self.full_name}! "
                f"Umeidhinishwa kuwa mshirika hai wa KKKT Mkwawa. "
                f"Kitambulisho chako cha uanachama ni {self.member_id}. "
                f"Tumia ID hii kuomba akaunti au kubadilisha nenosiri kupitia "
                f"https://www.kkktmkwawa.com/accounts/request-account/. "
                f"Karibu sana katika jumuiya yetu!"
            )
            response = send_sms(
                to=self.phone_number,
                message=approval_message,
                member=self
            )
            print(f"📩 Approval SMS sent to {self.phone_number}: {response}")
