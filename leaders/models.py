# leaders/models.py

import random
import string
from django.db import models
from django.utils.timezone import now
from members.models import ChurchMember

class Leader(models.Model):
    """
    Model to represent a church leader.
    A Leader is a ChurchMember.
    """

    leader_id = models.CharField(
        max_length=20,
        unique=True,
        blank=True,
        null=True,
        help_text="Unique 20-character ID with 10 digits and 10 lowercase letters."
    )

    # Updated Choice Fields
    OCCUPATION_CHOICES = [
        ('Parish Priest', 'Parish Priest'),
        ('Associate Priest', 'Associate Priest'),
        ('Deacon', 'Deacon'),
        ('Lay Ministers', 'Lay Ministers'),
        ('Catechists', 'Catechists'),
        ('Community Group Leaders', 'Community Group Leaders'),
        ('Parish Elders', 'Parish Elders'),
        ('Parish Office Staff', 'Parish Office Staff'),
        ('Parish Council Member', 'Parish Council Member'),
        ('Social Ministry Leader', 'Social Ministry Leader'),
        ('Parish Council Chairperson', 'Parish Council Chairperson'),
        ('Parish Council Secretary', 'Parish Council Secretary'),
        ('Parish Treasurer', 'Parish Treasurer'),
        ('Finance Committee Member', 'Finance Committee Member'),
        ('Development Committee Leader', 'Development Committee Leader'),
        ('Choir Leader', 'Choir Leader'),
        ('Parish Accountant', 'Parish Accountant'),
        ('Religious Education Leaders', 'Religious Education Leaders'),
        ('Hospitality Committee Chairperson', 'Hospitality Committee Chairperson'),
        ('Retreat and Training Committee Member', 'Retreat and Training Committee Member'),
        ('Youth Committee Members', 'Youth Committee Members'),
        ('Women\'s and Men\'s Committee Members', 'Women\'s and Men\'s Committee Members'),
        ('Senior Pastor', 'Senior Pastor'),
        ('Evangelist', 'Evangelist'),
    ]

    church_member = models.OneToOneField(
        ChurchMember,
        on_delete=models.CASCADE,
        related_name="leader",
        help_text="Select the church member who is a leader."
    )

    occupation = models.CharField(
        max_length=100, 
        choices=OCCUPATION_CHOICES,
        help_text="Occupation within the church."
    )
    start_date = models.DateField(help_text="Date when the leader started administration.")
    responsibilities = models.TextField(help_text="Responsibilities assigned to the leader.")
    time_in_service = models.CharField(
        max_length=100, blank=True, null=True, help_text="Time the leader has been in service."
    )

    # New date_created field
    date_created = models.DateTimeField(
        default=now,
        editable=False,
        help_text="Date and time when the leader record was created."
    )

    def __str__(self):
        return f"{self.church_member.full_name} - {self.occupation}"

    def generate_unique_leader_id(self):
        """
        Generates a highly randomized unique 20-character leader ID.
        - Mixes 10 random digits (0-9) and 10 random lowercase letters (a-z)
        - Ensures uniqueness across all Leaders
        """
        while True:
            numbers = ''.join(random.choices(string.digits, k=10))
            letters = ''.join(random.choices(string.ascii_lowercase, k=10))
            leader_id = ''.join(random.sample(numbers + letters, 20))  # Shuffle them randomly

            if not Leader.objects.filter(leader_id=leader_id).exists():
                return leader_id

    def save(self, *args, **kwargs):
        """
        Overrides the save method to ensure the unique leader_id is set before saving.
        """
        if not self.leader_id:  # Generate only if it's missing
            self.leader_id = self.generate_unique_leader_id()
        super().save(*args, **kwargs)