from django.db import models
from django.core.exceptions import ValidationError
from django.utils.timezone import now  # Importing timezone for automatic timestamp

class Year(models.Model):
    """
    Model to represent a year with a 'current' flag.
    Ensures only one year can be set to current at a time.
    Also ensures at least one year must be set as current.
    """

    YEAR_CHOICES = [(year, str(year)) for year in range(2020, 2081)]  # Updated range

    year = models.IntegerField(choices=YEAR_CHOICES, unique=True, help_text="Select a year from 2020 to 2080.")
    is_current = models.BooleanField(default=False, help_text="Set this year as the current year.")
    date_created = models.DateTimeField(default=now, help_text="Timestamp when the year was added.")

    def clean(self):
        """
        Custom validation:
        - Prevent setting future years as current.
        - Ensure at least one year is always set as current.
        """
        current_system_year = now().year  # Get the actual current year from the system

        if self.is_current and self.year > current_system_year:
            raise ValidationError(f"You cannot set {self.year} as the current year. The actual current year is {current_system_year}.")

        if not self.is_current:
            # Ensure at least one year remains current
            if not Year.objects.exclude(pk=self.pk).filter(is_current=True).exists():
                raise ValidationError("At least one year must be set as the current year.")

    def save(self, *args, **kwargs):
        self.clean()  # Run validation before saving

        if self.is_current:
            # If this year is set to current, set all other years to not current
            Year.objects.update(is_current=False)

        super().save(*args, **kwargs)

    def delete(self, *args, **kwargs):
        """
        Prevent deletion of the only current year.
        """
        if self.is_current:
            # Ensure another year exists as current before deleting
            if not Year.objects.exclude(pk=self.pk).filter(is_current=True).exists():
                raise ValidationError("You cannot delete the only current year. Set another year as current first.")

        super().delete(*args, **kwargs)

    def __str__(self):
        return f"{self.year} ({'Current' if self.is_current else 'Not Current'})"

import random
from django.db import models
from django.utils.timezone import now

class OutStation(models.Model):
    """
    Model to represent church outstations (replacing Zones/Kanda).
    """

    outstation_id = models.PositiveIntegerField(unique=True, blank=True, null=True, help_text="Randomly generated 6-digit ID for the outstation.")
    name = models.CharField(max_length=255, unique=True, help_text="Name of the outstation.")
    description = models.TextField(blank=True, null=True, help_text="Short description of the outstation.")
    location = models.CharField(max_length=255, help_text="Physical location of the outstation.")

    date_created = models.DateTimeField(default=now, help_text="Timestamp when the outstation was created.")
    date_updated = models.DateTimeField(auto_now=True, help_text="Timestamp when the outstation was last updated.")

    class Meta:
        ordering = ['name']  # Order outstations alphabetically

    def __str__(self):
        return f"{self.name} - {self.location}"

    def generate_unique_outstation_id(self):
        """
        Generates a unique 6-digit ID for the outstation.
        Ensures the ID is not already used.
        """
        while True:
            random_id = random.randint(100000, 999999)  # Generate a 6-digit number
            if not OutStation.objects.filter(outstation_id=random_id).exists():
                return random_id

    def save(self, *args, **kwargs):
        """
        Overrides the save method to ensure the unique outstation_id is set before saving.
        """
        if not self.outstation_id:  # Only generate if not already set
            self.outstation_id = self.generate_unique_outstation_id()
        super().save(*args, **kwargs)

class Cell(models.Model):
    """
    Model to represent cells (replacing Communities/Jumuiya) within an outstation.
    """
    cell_id = models.PositiveIntegerField(
        unique=True, blank=True, null=True, help_text="7-digit unique Cell ID"
    )
    name = models.CharField(max_length=255, unique=True, help_text="Name of the cell.")
    outstation = models.ForeignKey(
        OutStation, 
        on_delete=models.CASCADE, 
        related_name="cells", 
        help_text="Outstation this cell belongs to."
    )
    description = models.TextField(blank=True, null=True, help_text="Brief description of the cell.")
    location = models.CharField(max_length=255, help_text="Physical location of the cell.")
    date_created = models.DateTimeField(default=now, help_text="Timestamp when the cell was created.")
    date_updated = models.DateTimeField(auto_now=True, help_text="Timestamp when the cell was last updated.")

    class Meta:
        ordering = ['name']  # Order cells alphabetically

    def save(self, *args, **kwargs):
        """ Automatically generate a unique 7-digit cell_id if not set """
        if not self.cell_id:
            while True:
                new_id = random.randint(1000000, 9999999)  # Generate 7-digit ID
                if not Cell.objects.filter(cell_id=new_id).exists():
                    self.cell_id = new_id
                    break
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.name} ({self.outstation.name})"
    
import requests
from django.db import models
from django.core.exceptions import ValidationError

class ChurchLocation(models.Model):
    latitude = models.FloatField(help_text="Latitude coordinate of the church")
    longitude = models.FloatField(help_text="Longitude coordinate of the church")
    altitude = models.FloatField(blank=True, null=True, help_text="Altitude (optional, will be auto-calculated if left blank)")
    is_active = models.BooleanField(default=False, help_text="Mark this location as the active church location")

    def fetch_altitude(self):
        """
        Fetch the altitude for the given latitude and longitude using Open-Elevation API.
        """
        try:
            api_url = f"https://api.open-elevation.com/api/v1/lookup?locations={self.latitude},{self.longitude}"
            response = requests.get(api_url)
            if response.status_code == 200:
                data = response.json()
                altitude_value = data.get("results", [{}])[0].get("elevation", None)
                return altitude_value
            return None
        except Exception as e:
            print(f"⚠️ Error fetching altitude: {e}")
            return None

    def clean(self):
        """
        Prevents more than one ChurchLocation from being created.
        """
        if not self.pk and ChurchLocation.objects.exists():
            raise ValidationError("Only one ChurchLocation is allowed. Update the existing one instead.")

    def save(self, *args, **kwargs):
        """
        Ensures only one ChurchLocation exists at a time.
        If a new one is attempted, it raises an error.
        """
        if not self.pk and ChurchLocation.objects.exists():
            raise ValidationError("Only one ChurchLocation is allowed. Please update the existing one.")

        if not self.altitude:
            self.altitude = self.fetch_altitude()

        if self.is_active:
            # Ensure only one location is active
            ChurchLocation.objects.exclude(pk=self.pk).update(is_active=False)

        super().save(*args, **kwargs)

    def delete(self, *args, **kwargs):
        """
        Allows deleting the only location, which will then allow a new one to be created.
        """
        super().delete(*args, **kwargs)

    def __str__(self):
        return f"Church Location: ({self.latitude}, {self.longitude}, {self.altitude}) {'[Active]' if self.is_active else ''}"


