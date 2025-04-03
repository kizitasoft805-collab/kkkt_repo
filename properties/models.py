from django.db import models
from django.utils.timezone import now  # Import now function

class ChurchAsset(models.Model):
    """
    Model to store all assets of the church.
    """

    # Asset Type Choices
    ASSET_TYPE_CHOICES = [
        ('Building', 'Building'),
        ('Furniture', 'Furniture'),
        ('Electronics', 'Electronics'),
        ('Vehicle', 'Vehicle'),
        ('Stationery', 'Stationery'),
        ('Equipment', 'Equipment'),
        ('Consumables', 'Consumables'),
    ]

    # Quantity Name Choices
    QUANTITY_NAME_CHOICES = [
        ('Pieces', 'Pieces'),
        ('Boxes', 'Boxes'),
        ('Packets', 'Packets'),
        ('Bundles', 'Bundles'),
        ('Sets', 'Sets'),
        ('Rolls', 'Rolls'),
        ('Pads', 'Pads'),
        ('Reams', 'Reams'),
        ('Dozens', 'Dozens'),
        ('Liters', 'Liters'),
        ('Units', 'Units'),
        ('Pairs', 'Pairs'),
        ('Square meters', 'Square meters'),
        ('Shelves', 'Shelves'),
        ('Cubic meters', 'Cubic meters'),
        ('Kits', 'Kits'),
        ('Batteries', 'Batteries'),
        ('Packs', 'Packs'),
        ('Fleets', 'Fleets'),
        ('Plots', 'Plots'),
        ('Blocks', 'Blocks'),
        ('Complexes', 'Complexes'),
        ('Towers', 'Towers'),
        ('Halls', 'Halls'),
        ('Rooms', 'Rooms'),
        ('Floors', 'Floors'),
    ]

    # Status Choices
    STATUS_CHOICES = [
        ('Good', 'Good'),
        ('Needs Repair', 'Needs Repair'),
        ('Damaged', 'Damaged'),
        ('Sold', 'Sold'),
        ('Donated', 'Donated'),
    ]

    # Asset Details
    name = models.CharField(max_length=255, help_text="Name of the asset.")
    asset_type = models.CharField(
        max_length=20, choices=ASSET_TYPE_CHOICES, help_text="Type of asset."
    )
    description = models.TextField(
        blank=True, null=True, help_text="Short description of the asset."
    )
    acquisition_date = models.DateField(
        blank=True, null=True, help_text="Date the asset was acquired (optional)."
    )

    # Quantity Details
    quantity_name = models.CharField(
        max_length=50, choices=QUANTITY_NAME_CHOICES,
        help_text="Unit of measurement (e.g., dozen, set, piece, etc.).",
    )
    quantity = models.PositiveIntegerField(default=1, help_text="Number of units.")

    # Asset Condition
    status = models.CharField(
        max_length=20, choices=STATUS_CHOICES, help_text="Current condition of the asset."
    )

    # Financial Value
    value = models.DecimalField(
        max_digits=12, decimal_places=2, help_text="Estimated value of the asset (in currency)."
    )

    # ⏳ Timestamp Field (Automatically Set When Created)
    created_at = models.DateTimeField(default=now, editable=False, help_text="Date and time when the asset was added.")

    def __str__(self):
        return f"{self.name} ({self.asset_type}) - {self.status}"

    class Meta:
        ordering = ['-created_at']  # Show newest assets first
        verbose_name = "Church Asset"
        verbose_name_plural = "Church Assets"

from django.db import models
from .models import ChurchAsset  # Import the ChurchAsset model

class ChurchAssetMedia(models.Model):
    """
    Model to store media files (images) related to Church Assets.
    """

    church_asset = models.ForeignKey(
        ChurchAsset, 
        on_delete=models.CASCADE, 
        related_name="media",
        help_text="The asset this media file is associated with."
    )
    image = models.ImageField(
        upload_to="church_assets/",
        help_text="Upload an image of the church asset."
    )
    uploaded_at = models.DateTimeField(
        auto_now_add=True, help_text="The date and time this media was uploaded."
    )

    def __str__(self):
        return f"Media for {self.church_asset.name} (Uploaded on {self.uploaded_at})"

    class Meta:
        ordering = ["-uploaded_at"]  # Show latest uploads first
        verbose_name = "Church Asset Media"
        verbose_name_plural = "Church Asset Media"
