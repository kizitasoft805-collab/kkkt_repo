# finance/forms.py
from django import forms
from django.utils.timezone import now
from settings.models import Year
from members.models import ChurchMember
from finance.models import Pledge

class MemberPledgeForm(forms.ModelForm):
    """
    A special Pledge form for CHURCH_MEMBER users to pledge for themselves.
    The member field is set automatically.
    """

    # We reuse MONTH_CHOICES if needed:
    MONTH_CHOICES = [
        ('January', 'January'), ('February', 'February'), ('March', 'March'),
        ('April', 'April'), ('May', 'May'), ('June', 'June'),
        ('July', 'July'), ('August', 'August'), ('September', 'September'),
        ('October', 'October'), ('November', 'November'), ('December', 'December')
    ]

    envelope_number = forms.CharField(
        max_length=50,
        label="Envelope Number",
        widget=forms.TextInput(attrs={'placeholder': 'Envelope Number'})
    )
    pledge_amount = forms.DecimalField(
        max_digits=10,
        decimal_places=2,
        label="Pledge Amount",
        widget=forms.NumberInput(attrs={'placeholder': 'Amount for this pledge'})
    )
    pledge_for_construction = forms.DecimalField(
        max_digits=10,
        decimal_places=2,
        label="Pledge for Construction",
        widget=forms.NumberInput(attrs={'placeholder': 'Amount for construction'})
    )
    year = forms.ModelChoiceField(
        queryset=Year.objects.all(),
        label="Year"
    )
    month = forms.ChoiceField(
        choices=MONTH_CHOICES,
        label="Month"
    )
    date_given = forms.DateField(
        label="Date Given",
        widget=forms.DateInput(attrs={'type': 'date'})
    )

    class Meta:
        model = Pledge
        # We exclude 'member' because it's automatically set
        # We also exclude 'date_created', 'date_updated', etc.
        exclude = [
            'member', 'date_created', 'date_updated',
        ]

    def __init__(self, *args, **kwargs):
        # We’ll accept a 'member' kwarg from the view if we want to attach a specific member
        member = kwargs.pop('member', None)
        super().__init__(*args, **kwargs)

        # Default year -> The "current" Year record
        current_year = Year.objects.filter(is_current=True).first()
        if current_year:
            self.fields['year'].initial = current_year

        # Default month -> current month string
        self.fields['month'].initial = now().strftime('%B')

        # Default date -> today
        self.fields['date_given'].initial = now().date()

        # If we want to store 'member' in the form instance, we can do so:
        self.member_instance = member  # For reference if needed

    def save(self, commit=True):
        pledge = super().save(commit=False)
        # Assign the correct church member automatically
        if hasattr(self, 'member_instance') and self.member_instance:
            pledge.member = self.member_instance
        # Save the pledge
        if commit:
            pledge.save()
        return pledge
