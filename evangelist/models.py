# evangelist/models.py
from django.db import models
from django.utils.timezone import now
from leaders.models import Leader


class EvangelistReport(models.Model):
    """
    Head‑count and cash‑breakdown for a single worship service.
    """

    # ─────────────── Attendance ───────────────
    children_count = models.PositiveIntegerField(
        help_text="Number of children present."
    )
    adults_count = models.PositiveIntegerField(
        help_text="Number of adults present."
    )

    # ─────────────── Cash breakdown (TZS) ───────────────
    count_10000 = models.PositiveIntegerField(default=0, help_text="Number of 10,000 TZS notes.")
    count_5000  = models.PositiveIntegerField(default=0, help_text="Number of 5,000 TZS notes.")
    count_2000  = models.PositiveIntegerField(default=0, help_text="Number of 2,000 TZS notes.")
    count_1000  = models.PositiveIntegerField(default=0, help_text="Number of 1,000 TZS notes.")
    count_500   = models.PositiveIntegerField(default=0, help_text="Number of 500 TZS coins.")
    count_200   = models.PositiveIntegerField(default=0, help_text="Number of 200 TZS coins.")
    count_100   = models.PositiveIntegerField(default=0, help_text="Number of 100 TZS coins.")
    count_50    = models.PositiveIntegerField(default=0, help_text="Number of 50 TZS coins.")

    # ─────────────── Date field ───────────────
    date_given = models.DateField(
        default=now,
        help_text="Date the offering was given (defaults to today)."
    )

    # ─────────────── Timestamps ───────────────
    date_created = models.DateTimeField(auto_now_add=True)
    date_updated = models.DateTimeField(auto_now=True)

    # ─────────────── Convenience properties ───────────────
    @property
    def total_cash(self) -> int:
        """
        Returns the total cash amount in Tanzanian shillings.
        """
        return (
            self.count_10000 * 10000 +
            self.count_5000  * 5000  +
            self.count_2000  * 2000  +
            self.count_1000  * 1000  +
            self.count_500   * 500   +
            self.count_200   * 200   +
            self.count_100   * 100   +
            self.count_50    * 50
        )

    @property
    def total_attendance(self) -> int:
        return self.children_count + self.adults_count

    def __str__(self):
        return f"{self.date_given} – {self.total_attendance} attendees – TZS {self.total_cash:,}"

    class Meta:
        ordering = ["-date_given"]
        verbose_name = "Evangelist Report"
        verbose_name_plural = "Evangelist Reports"


class ElderDuty(models.Model):
    """
    Associates one or more elders with a specific EvangelistReport.
    Only leaders whose occupation is 'Elder' appear in the dropdown.
    """

    evangelist_report = models.ForeignKey(
        EvangelistReport,
        on_delete=models.CASCADE,
        related_name="elder_duties",
        help_text="The evangelist report this duty record belongs to."
    )

    elder = models.ForeignKey(
        Leader,
        on_delete=models.PROTECT,
        limit_choices_to={"occupation": "Elder"},
        related_name="elder_duties",
        help_text="Select an elder who was on duty."
    )

    # (Optional) timestamp for record‑keeping
    date_created = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.elder} – {self.evangelist_report.date_given}"

    class Meta:
        unique_together = ("evangelist_report", "elder")
        verbose_name = "Elder on Duty"
        verbose_name_plural = "Elders on Duty"
