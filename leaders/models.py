# leaders/models.py

import random
import string
from django.db import models
from django.utils.timezone import now

from members.models import ChurchMember
from settings.models import OutStation


class Leader(models.Model):
    """
    Church‑leader model tailored for an evangelical congregation.
    """

    # ────────────────────────────────────────────────────────────
    # Core identifiers
    # ────────────────────────────────────────────────────────────
    leader_id = models.CharField(
        max_length=20,
        unique=True,
        blank=True,
        null=True,
        help_text="Unique 20‑character ID with 10 digits + 10 lowercase letters."
    )

    # ────────────────────────────────────────────────────────────
    # Comprehensive occupation list (Evangelical context)
    # ────────────────────────────────────────────────────────────
    OCCUPATION_CHOICES = [
        # Pastoral / preaching
        ("Senior Pastor",             "Senior Pastor"),
        ("Associate Pastor",          "Associate Pastor"),
        ("Assistant Pastor",          "Assistant Pastor"),
        ("Youth Pastor",              "Youth Pastor"),
        ("Children’s Pastor",         "Children’s Pastor"),
        ("Evangelist",                "Evangelist"),
        ("Missionary",                "Missionary"),

        # Governance & board
        ("Chairperson",               "Chairperson"),
        ("Vice Chairperson",          "Vice Chairperson"),
        ("Secretary",                 "Secretary"),
        ("Assistant Secretary",       "Assistant Secretary"),
        ("Board Chair",               "Board Chair"),
        ("Board Secretary",           "Board Secretary"),
        ("Elder",                     "Elder"),
        ("Chief Elder",               "Chief Elder"),
        ("Deacon",                    "Deacon"),
        ("Deaconess",                 "Deaconess"),
        ("Steward",                   "Steward"),

        # Worship & discipleship
        ("Worship Leader",            "Worship Leader"),
        ("Choir Director",            "Choir Director"),
        ("Praise Team Leader",        "Praise Team Leader"),
        ("Sunday School Teacher",     "Sunday School Teacher"),
        ("Bible Study Leader",        "Bible Study Leader"),
        ("Small Group Leader",        "Small Group Leader"),

        # Ministry department heads
        ("Youth Coordinator",         "Youth Coordinator"),
        ("Women’s Ministry Leader",   "Women’s Ministry Leader"),
        ("Men’s Ministry Leader",     "Men’s Ministry Leader"),
        ("Prayer Coordinator",        "Prayer Coordinator"),
        ("Intercessory Leader",       "Intercessory Leader"),
        ("Outreach Coordinator",      "Outreach Coordinator"),
        ("Missions Coordinator",      "Missions Coordinator"),
        ("Social Ministry Leader",    "Social Ministry Leader"),
        ("Hospitality Coordinator",   "Hospitality Coordinator"),
        ("Ushering Coordinator",      "Ushering Coordinator"),
        ("Security Coordinator",      "Security Coordinator"),
        ("Maintenance Supervisor",    "Maintenance Supervisor"),
        ("Welfare Coordinator",       "Welfare Coordinator"),
        ("Media/Tech Team Lead",      "Media/Tech Team Lead"),
        ("Communications Officer",    "Communications Officer"),

        # Finance & administration
        ("Church Treasurer",          "Church Treasurer"),
        ("Church Accountant",         "Church Accountant"),
        ("Administrator",             "Administrator"),

        # Advisory / honorary
        ("Patron",                    "Patron"),
        ("Matron",                    "Matron"),
        ("Advisor",                   "Advisor"),
    ]

    # ────────────────────────────────────────────────────────────
    # Relational fields
    # ────────────────────────────────────────────────────────────
    church_member = models.OneToOneField(
        ChurchMember,
        on_delete=models.CASCADE,
        related_name="leader",
        help_text="Select the church member who serves as a leader."
    )

    occupation = models.CharField(
        max_length=100,
        choices=OCCUPATION_CHOICES,
        help_text="Role / office held within the church."
    )

    start_date = models.DateField(help_text="Date this leader began serving.")
    responsibilities = models.TextField(help_text="Key duties and ministry scope.")
    time_in_service = models.CharField(
        max_length=100,
        blank=True,
        null=True,
        help_text="Human‑readable duration in service (e.g., '3 years')."
    )

    # Optional except for Evangelists
    outstation = models.ForeignKey(
        OutStation,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        help_text="Out‑station assignment (required for Evangelists)."
    )

    date_created = models.DateTimeField(
        default=now,
        editable=False,
        help_text="Timestamp when this record was created."
    )

    # ────────────────────────────────────────────────────────────
    # String representation
    # ────────────────────────────────────────────────────────────
    def __str__(self):
        return f"{self.church_member.full_name} – {self.occupation}"

    # ────────────────────────────────────────────────────────────
    # Helper: unique ID generator
    # ────────────────────────────────────────────────────────────
    def generate_unique_leader_id(self) -> str:
        """
        Produce a 20‑character ID (10 random digits + 10 random letters).
        """
        while True:
            digits = ''.join(random.choices(string.digits, k=10))
            letters = ''.join(random.choices(string.ascii_lowercase, k=10))
            candidate = ''.join(random.sample(digits + letters, 20))
            if not Leader.objects.filter(leader_id=candidate).exists():
                return candidate

    # ────────────────────────────────────────────────────────────
    # Save override for ID + validation
    # ────────────────────────────────────────────────────────────
    def save(self, *args, **kwargs):
        # Auto‑generate ID once
        if not self.leader_id:
            self.leader_id = self.generate_unique_leader_id()

        # Evangelists must have an out‑station
        if self.occupation == "Evangelist" and not self.outstation:
            raise ValueError("An Evangelist must be assigned to an out‑station.")

        super().save(*args, **kwargs)
