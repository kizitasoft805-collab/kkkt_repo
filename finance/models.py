# finance/models.py

from django.db import models
from django.utils.timezone import now

class OfferingCategory(models.Model):
    """
    Model to represent an Offering Category with a name, description,
    and timestamps (date created & date updated).
    """

    name = models.CharField(
        max_length=255,
        unique=True,
        help_text="Unique name of the offering category (e.g., 'Sunday Mass Offering', 'Fundraising', etc.)."
    )
    description = models.TextField(
        blank=True,
        null=True,
        help_text="Additional details or notes about this offering category."
    )

    # Automatically store creation date/time
    date_created = models.DateTimeField(
        auto_now_add=True,
        help_text="Timestamp when this offering category was created."
    )
    # Automatically store update date/time
    date_updated = models.DateTimeField(
        auto_now=True,
        help_text="Timestamp when this offering category was last updated."
    )

    def __str__(self):
        """Return the name for a readable representation."""
        return self.name

    class Meta:
        ordering = ["name"]  # e.g., sort by name in ascending order
        verbose_name = "Offering Category"
        verbose_name_plural = "Offering Categories"

from django.db import models
from django.utils.timezone import now
from members.models import ChurchMember
from settings.models import Year, OutStation  # Import OutStation
from finance.models import OfferingCategory

class Offerings(models.Model):
    """
    Model to manage all church offerings.
    """

    SERVICE_TIME_CHOICES = [
        ('Morning', 'Morning'),
        ('Afternoon', 'Afternoon'),
        ('Evening', 'Evening'),
        ('Night', 'Night'),
    ]

    # 📅 Year (Automatically Set to the Current Year)
    year = models.ForeignKey(
        Year, 
        on_delete=models.PROTECT, 
        null=True, 
        blank=True,
        related_name="offerings",
        help_text="The year in which this offering was recorded."
    )

    # 📅 Date Given (Default: Today)
    date_given = models.DateField(
        default=now,
        help_text="The date offering was given. Displays the day of the week."
    )

    # ⏰ Service Time
    service_time = models.CharField(
        max_length=10,
        choices=SERVICE_TIME_CHOICES,
        help_text="The service during which the offering was collected."
    )

    # 💰 Amount Collected
    amount = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        help_text="Total amount of money collected."
    )

    # 👤 Collected By (Church Member)
    collected_by = models.ForeignKey(
        ChurchMember,
        on_delete=models.SET_NULL,
        null=True,
        related_name="offerings_collected",
        help_text="The church member who collected the offering."
    )

    # 📝 Recorded By (Church Member)
    recorded_by = models.ForeignKey(
        ChurchMember,
        on_delete=models.SET_NULL,
        null=True,
        related_name="offerings_recorded",
        help_text="The church member who recorded the offering."
    )

    # 📖 Mass Name
    mass_name = models.CharField(
        max_length=255,
        help_text="The name of the mass during which the offering was collected."
    )

    # 🗒️ Notes
    notes = models.TextField(
        blank=True,
        null=True,
        help_text="Additional details or notes about this offering."
    )

    # ✅ Offering Category with CASCADE
    offering_category = models.ForeignKey(
        OfferingCategory,
        on_delete=models.CASCADE,    # If category is deleted, offerings also get deleted
        related_name="offerings",
        help_text="Category under which this offering is classified."
    )

    # 🏛️ Outstation (Foreign Key to OutStation)
    outstation = models.ForeignKey(
        OutStation,
        on_delete=models.PROTECT,  # Prevent deletion of OutStation if linked to offerings
        related_name="offerings",
        help_text="The outstation where this offering was collected."
    )

    # ⏳ Date Created (Auto Now)
    date_created = models.DateTimeField(
        auto_now_add=True,
        help_text="The date and time when this offering was recorded."
    )

    # 🕒 Date Updated (Auto Now)
    date_updated = models.DateTimeField(
        auto_now=True,
        help_text="The date and time when this offering was last updated."
    )

    def save(self, *args, **kwargs):
        """
        Ensure that the offering is assigned to the current year automatically if not provided.
        """
        if not self.year:
            current_year = Year.objects.filter(is_current=True).first()
            if current_year:
                self.year = current_year
        super().save(*args, **kwargs)

    def __str__(self):
        return (
            f"{self.mass_name} - "
            f"{self.date_given.strftime('%A, %d %B %Y')} - "
            f"{self.service_time} - "
            f"{self.amount} TZS - "
            f"{self.outstation.name}"
        )

import random
import string
from datetime import timedelta
from django.db import models
from django.utils.timezone import now
from django.core.validators import MinValueValidator
from properties.models import ChurchAsset
from settings.models import Year


class FacilityRenting(models.Model):
    """
    Model to store facility renting details for church assets.
    """

    # 📅 Year ForeignKey
    year = models.ForeignKey(
        Year,
        on_delete=models.PROTECT,
        related_name='facility_rentings',
        help_text="The year this renting belongs to."
    )

    # 🔗 ForeignKey to ChurchAsset
    property_rented = models.ForeignKey(
        ChurchAsset,
        on_delete=models.CASCADE,
        related_name='facility_rentings',
        help_text="The church asset that is being rented."
    )

    # 👤 Name of the Rentor
    rentor_name = models.CharField(
        max_length=255,
        help_text="Name of the person renting the asset."
    )

    # 💰 Amount in TZS
    amount = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        validators=[MinValueValidator(0)],
        help_text="Rental amount in Tanzanian Shillings (TZS)"
    )

    # 📅 Date Rented
    date_rented = models.DateField(
        default=now,
        help_text="Date when the asset was rented."
    )

    # 📅 End Date (New Field)
    end_date = models.DateField(
        blank=True,
        null=True,
        help_text="Date when the rental period ends."
    )

    # 🎯 Purpose of Renting
    purpose = models.TextField(
        blank=True,
        null=True,
        help_text="Purpose for renting the facility."
    )

    # 🧾 Receipt ID (Automatically Generated)
    receipt_id = models.CharField(
        max_length=10,
        unique=True,
        editable=False,
        help_text="Automatically generated receipt ID (5 numbers + 5 uppercase letters)."
    )

    # 📅 Date Created (Auto-filled)
    date_created = models.DateTimeField(
        auto_now_add=True,
        help_text="Timestamp when the renting record was created."
    )

    # 📅 Date Updated (Auto-updated)
    date_updated = models.DateTimeField(
        auto_now=True,
        help_text="Timestamp when the renting record was last updated."
    )

    def __str__(self):
        return f"Renting: {self.property_rented.name} by {self.rentor_name} - TZS {self.amount:,.2f}"

    def generate_receipt_id(self):
        """
        Generates a unique 10-character receipt ID:
        - 5 random digits (1-9)
        - 5 random uppercase letters (A-Z)
        - Shuffled to ensure randomness
        """
        while True:
            digits = ''.join(random.choices('123456789', k=5))
            letters = ''.join(random.choices(string.ascii_uppercase, k=5))
            combined = list(digits + letters)
            random.shuffle(combined)
            receipt_id = ''.join(combined)

            if not FacilityRenting.objects.filter(receipt_id=receipt_id).exists():
                return receipt_id

    def rental_duration(self):
        """
        Calculates the duration between the date_rented and end_date.
        Returns duration in a human-readable format.
        """
        if self.end_date:
            delta = self.end_date - self.date_rented
            total_seconds = delta.total_seconds()

            if total_seconds < 60:
                return f"{int(total_seconds)} seconds"
            elif total_seconds < 3600:
                return f"{int(total_seconds // 60)} minutes"
            elif total_seconds < 86400:
                return f"{int(total_seconds // 3600)} hours"
            elif total_seconds < 604800:
                return f"{int(total_seconds // 86400)} days"
            elif total_seconds < 2592000:
                return f"{int(total_seconds // 604800)} weeks"
            elif total_seconds < 31536000:
                return f"{int(total_seconds // 2592000)} months"
            else:
                return f"{int(total_seconds // 31536000)} years"
        return "N/A"

    def save(self, *args, **kwargs):
        """
        Overrides the save method to:
        - Automatically generate a unique receipt ID when creating a new renting record
        - Set the current year if not provided
        """
        if not self.receipt_id:
            self.receipt_id = self.generate_receipt_id()

        # Set the current year if not already set
        if not self.year_id:
            try:
                current_year = Year.objects.get(is_current=True)
                self.year = current_year
            except Year.DoesNotExist:
                raise ValueError("No current year is set in the system.")

        super().save(*args, **kwargs)

    class Meta:
        ordering = ['-date_rented']
        verbose_name = "Facility Renting"
        verbose_name_plural = "Facility Rentings"


from django.db import models
from django.utils.timezone import now

class SpecialContribution(models.Model):
    """
    Model to store special contribution details for church finances.
    """

    # Choices for Contribution Type
    CONTRIBUTION_TYPE_CHOICES = [
        ("DIOCESAN", "Special Diocesan contributions"),
        ("JIMBO", "Jimbo contributions"),
        ("FELLOWSHIP", "Fellowship contributions"),
    ]

    # 📌 NEW FIELD: Contribution Type
    contribution_type = models.CharField(
        max_length=20,
        choices=CONTRIBUTION_TYPE_CHOICES,
        default="JIMBO",  # You can choose a default if needed
        help_text="Type of special contribution (Diocesan, Jimbo, or Parish)."
    )

    # 📝 Name of the Special Contribution
    name = models.CharField(
        max_length=255,
        unique=True,
        help_text="The name of the special contribution (e.g., Church Renovation Fund, Charity Drive, etc.)."
    )

    # 📋 Description of the Contribution
    description = models.TextField(
        blank=True,
        null=True,
        help_text="A brief description of the purpose or details of the special contribution."
    )

    # 📅 Date Created (Auto-filled)
    date_created = models.DateTimeField(
        auto_now_add=True,
        help_text="Timestamp when the special contribution record was created."
    )

    # 📅 Date Updated (Auto-updated)
    date_updated = models.DateTimeField(
        auto_now=True,
        help_text="Timestamp when the special contribution record was last updated."
    )

    def __str__(self):
        return f"{self.get_contribution_type_display()} - {self.name}"

    class Meta:
        ordering = ['-date_created']
        verbose_name = "Special Contribution"
        verbose_name_plural = "Special Contributions"


from django.db import models
from django.utils.timezone import now
from settings.models import Year
from finance.models import SpecialContribution

class DonationItemFund(models.Model):
    """
    Model to store donation item fund details linked to a special contribution and year.
    """

    # 🔗 ForeignKey to SpecialContribution
    contribution_type = models.ForeignKey(
        SpecialContribution,
        on_delete=models.CASCADE,
        related_name='donation_item_funds',
        help_text="The special contribution this donation item fund belongs to."
    )

    # 📅 ForeignKey to Year (Automatically set to the current year)
    year = models.ForeignKey(
        Year,
        on_delete=models.PROTECT,
        related_name='donation_item_funds',
        help_text="The year this donation item fund belongs to."
    )

    # 📆 Period of the Donation
    period = models.CharField(
        max_length=100,
        help_text="The period associated with this donation (e.g., Q1 2024, January 2024, etc.)."
    )

    # ⛪ Mass Name
    mass_name = models.CharField(
        max_length=255,
        help_text="The name of the mass or event where this donation was made."
    )

    # 💰 Amount Obtained (NEW FIELD)
    amount = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        help_text="The amount obtained from this donation."
    )

    # 📝 Notes
    notes = models.TextField(
        blank=True,
        null=True,
        help_text="Additional notes or remarks related to the donation."
    )

    # 📅 Date Created
    date_created = models.DateTimeField(
        auto_now_add=True,
        help_text="Timestamp when the donation item fund was created."
    )

    # 📅 Date Updated
    date_updated = models.DateTimeField(
        auto_now=True,
        help_text="Timestamp when the donation item fund was last updated."
    )

    def save(self, *args, **kwargs):
        """
        Automatically assign the current year if not provided.
        """
        if not self.year_id:
            try:
                current_year = Year.objects.get(is_current=True)
                self.year = current_year
            except Year.DoesNotExist:
                raise ValueError("No current year is set in the system.")
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.mass_name} - {self.period} ({self.contribution_type.name})"

    class Meta:
        ordering = ['-date_created']
        verbose_name = "Donation Item Fund"
        verbose_name_plural = "Donation Item Funds"

from django.db import models
from django.utils.timezone import now
from settings.models import Year
from members.models import ChurchMember


class Pledge(models.Model):
    """
    Model to represent a financial pledge made by a church member.
    """

    # Months choices
    MONTH_CHOICES = [
        ('January', 'January'), ('February', 'February'), ('March', 'March'),
        ('April', 'April'), ('May', 'May'), ('June', 'June'),
        ('July', 'July'), ('August', 'August'), ('September', 'September'),
        ('October', 'October'), ('November', 'November'), ('December', 'December')
    ]

    member = models.ForeignKey(
        ChurchMember,
        on_delete=models.CASCADE,
        related_name="pledges",
        help_text="The church member making the pledge."
    )
    envelope_number = models.CharField(
        max_length=50,
        help_text="Envelope number used for the pledge."
    )
    pledge_amount = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        help_text="The pledged amount."
    )
    pledge_for_construction = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        help_text="The amount pledged specifically for construction."
    )
    year = models.ForeignKey(
        Year,
        on_delete=models.CASCADE,
        related_name="pledges",
        help_text="The year in which the pledge was made."
    )
    month = models.CharField(
        max_length=10,
        choices=MONTH_CHOICES,
        help_text="The month in which the pledge was made."
    )
    date_given = models.DateField(
        help_text="The date when the pledge was given."
    )
    date_created = models.DateTimeField(
        default=now,
        editable=False,
        help_text="The date and time when the pledge record was created."
    )
    date_updated = models.DateTimeField(
        auto_now=True,
        help_text="The date and time when the pledge record was last updated."
    )

    def __str__(self):
        return f"{self.member.full_name} - {self.pledge_amount} ({self.year.year}, {self.month})"


from django.db import models

class Category(models.Model):
    """
    Model to represent a Category with a name, description, and timestamps.
    """

    name = models.CharField(
        max_length=255,
        unique=True,
        help_text="Unique category name (e.g., 'Construction Projects', 'Fundraising', etc.)."
    )
    description = models.TextField(
        blank=True,
        null=True,
        help_text="Brief description or overview of this category."
    )

    # 📅 Date Created (Auto-filled)
    date_created = models.DateTimeField(
        auto_now_add=True,
        help_text="Timestamp when this category was first created."
    )

    # 📅 Date Updated (Auto-updated)
    date_updated = models.DateTimeField(
        auto_now=True,
        help_text="Timestamp when this category was last updated."
    )

    def __str__(self):
        return self.name

    class Meta:
        ordering = ["name"]
        verbose_name = "Category"
        verbose_name_plural = "Categories"

from django.db import models
from django.utils.timezone import now
from settings.models import Year
from finance.models import Category

class Expenditure(models.Model):
    """
    Model to track expenditures, linked to a specific year, month,
    date taken, category, an expenditure amount, with optional 
    receipt, purpose, and notes.
    """

    # Choices for Month
    MONTH_CHOICES = [
        ("January", "January"),
        ("February", "February"),
        ("March", "March"),
        ("April", "April"),
        ("May", "May"),
        ("June", "June"),
        ("July", "July"),
        ("August", "August"),
        ("September", "September"),
        ("October", "October"),
        ("November", "November"),
        ("December", "December"),
    ]

    # 🔗 Link to Year
    year = models.ForeignKey(
        Year,
        on_delete=models.PROTECT,
        related_name='expenditures',
        help_text="The year this expenditure is associated with."
    )

    # 🗓 Month as a choice field
    month = models.CharField(
        max_length=15,
        choices=MONTH_CHOICES,
        help_text="Select the month for this expenditure."
    )

    # 📅 Date the money was spent, defaulting to now but editable by user
    date_taken = models.DateTimeField(
        default=now,
        help_text="Date when the expenditure was taken (default is now)."
    )

    # 💰 Expenditure amount (use DecimalField for currency data)
    expenditure_amount = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        help_text="Amount of money spent."
    )

    # 🏷 Optional short purpose or title for this expenditure
    expenditure_purpose = models.CharField(
        max_length=255,
        blank=True,
        null=True,
        help_text="Brief purpose or title for this expenditure (optional)."
    )

    # 🗒 Detailed notes about the expenditure
    notes = models.TextField(
        blank=True,
        null=True,
        help_text="Additional notes or remarks regarding this expenditure (optional)."
    )

    # 📄 Receipt or Document (Optional)
    receipt = models.FileField(
        upload_to="receipt_uploads/",
        blank=True,
        null=True,
        help_text="Upload a receipt or supporting document for this expenditure (PDF, image, etc.)."
    )

    # 📅 Date Created (Auto-filled)
    date_created = models.DateTimeField(
        auto_now_add=True,
        help_text="Timestamp when this record was created."
    )

    # 📅 Date Updated (Auto-updated)
    date_updated = models.DateTimeField(
        auto_now=True,
        help_text="Timestamp when this record was last updated."
    )

    # 🏷 Category foreign key
    category = models.ForeignKey(
        Category,
        on_delete=models.CASCADE,
        related_name='expenditures',
        help_text="The category under which this expenditure falls."
    )

    def __str__(self):
        """
        Show a brief summary including the category name, month/year, and amount.
        If there's a purpose, you could optionally include it as well.
        """
        return f"{self.category.name} - {self.month} {self.year.year}: {self.expenditure_amount}"

    class Meta:
        ordering = ['-date_created']
        verbose_name = "Expenditure"
        verbose_name_plural = "Expenditures"
