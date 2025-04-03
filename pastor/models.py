from django.db import models
from django.conf import settings  # or from settings.models import Year if needed
from django.utils.timezone import now

# If using a separate 'settings' app for Year, adjust the import accordingly:
# from settings.models import Year

MONTH_CHOICES = [
    ('January', 'January'),
    ('February', 'February'),
    ('March', 'March'),
    ('April', 'April'),
    ('May', 'May'),
    ('June', 'June'),
    ('July', 'July'),
    ('August', 'August'),
    ('September', 'September'),
    ('October', 'October'),
    ('November', 'November'),
    ('December', 'December'),
]


class PastorReport(models.Model):
    """
    Model to store the pastor's monthly report.
    """

    month = models.CharField(
        max_length=20,
        choices=MONTH_CHOICES,
        help_text="Select the month for this report."
    )

    # If your Year model is in settings.models:
    # from settings.models import Year
    year = models.ForeignKey(
        'settings.Year',
        on_delete=models.PROTECT,
        help_text="Select the reporting year."
    )

    number_of_evangelists = models.PositiveIntegerField(
        help_text="Number of evangelists."
    )

    number_of_local_congregations = models.PositiveIntegerField(
        help_text="Total local congregations in the parish."
    )

    local_congregations_lords_table = models.PositiveIntegerField(
        help_text="Number of congregations where you administered the Lord’s Table."
    )

    baptized_male = models.PositiveIntegerField(
        default=0,
        help_text="Number of males baptized."
    )
    baptized_female = models.PositiveIntegerField(
        default=0,
        help_text="Number of females baptized."
    )

    returned_male = models.PositiveIntegerField(
        default=0,
        help_text="Number of returning male Christians."
    )
    returned_female = models.PositiveIntegerField(
        default=0,
        help_text="Number of returning female Christians."
    )

    marriages_solemnized = models.PositiveIntegerField(
        default=0,
        help_text="Total number of marriages officiated."
    )

    membership_transfer_sessions_count = models.PositiveIntegerField(
        default=0,
        help_text="How many times you taught membership transfer sessions."
    )
    membership_transfer_sessions_where = models.TextField(
        blank=True,
        help_text="Where those membership transfer sessions were conducted."
    )

    number_of_christians = models.PositiveIntegerField(
        default=0,
        help_text="Number of Christians in total."
    )

    number_of_cell_groups = models.PositiveIntegerField(
        default=0,
        help_text="Number of cell groups in the parish."
    )

    church_projects = models.TextField(
        blank=True,
        help_text="Details of ongoing church/parish projects."
    )

    number_of_joined_christians = models.PositiveIntegerField(
        default=0,
        help_text="Number of new Christians who joined."
    )

    number_of_deceased_christians = models.PositiveIntegerField(
        default=0,
        help_text="Number of Christians who passed on to glory."
    )

    number_of_separated_christians = models.PositiveIntegerField(
        default=0,
        help_text="Number of Christians who left (separated from) the church."
    )

    number_of_relocated_christians = models.PositiveIntegerField(
        default=0,
        help_text="Number of Christians who relocated."
    )

    average_income_this_month = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        default=0.00,
        help_text="Average total monthly income."
    )

    number_of_schools = models.PositiveIntegerField(
        default=0,
        help_text="Number of schools within this parish."
    )

    parish_meetings = models.TextField(
        blank=True,
        help_text="Specify committees and when they met."
    )

    growth_explanations = models.TextField(
        blank=True,
        help_text="Explanations fostering spiritual, numerical, and economic growth."
    )

    # New fields
    date_created = models.DateTimeField(
        auto_now_add=True,
        help_text="Date and time this report was created (set automatically)."
    )

    date_updated = models.DateTimeField(
        auto_now=True,
        help_text="Date and time this report was last updated (auto)."
    )

    def __str__(self):
        return f"{self.month} {self.year.year} Report"


class DatesOfServices(models.Model):
    """
    Model to store multiple service dates under one PastorReport.
    """
    pastor_report = models.ForeignKey(
        PastorReport,
        on_delete=models.CASCADE,
        related_name='dates_of_services'
    )
    service_date = models.DateField(
        help_text="Date of the service."
    )

    def __str__(self):
        return f"Service on {self.service_date} (Report: {self.pastor_report})"


class VisitedLocalCongregation(models.Model):
    """
    Model to store multiple local congregations visited under one PastorReport.
    """
    pastor_report = models.ForeignKey(
        PastorReport,
        on_delete=models.CASCADE,
        related_name='visited_congregations'
    )
    congregation_name = models.CharField(
        max_length=100,
        help_text="Name of the local congregation/sub-parish visited."
    )

    def __str__(self):
        return f"{self.congregation_name} (Report: {self.pastor_report})"

