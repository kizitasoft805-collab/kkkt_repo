# forms.py
from django import forms
from django.forms import inlineformset_factory
from django.utils import timezone

from .models import PastorReport, DatesOfServices, VisitedLocalCongregation
from settings.models import Year  # Adjust if your Year model is elsewhere

class PastorReportForm(forms.ModelForm):
    """
    Main form for creating/updating a PastorReport instance
    with custom widgets and default (initial) values for
    the 'year' and 'month' fields.
    """
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # 1) Set default year to the one with is_current=True
        try:
            current_year = Year.objects.get(is_current=True)
            self.fields['year'].initial = current_year.pk
        except Year.DoesNotExist:
            pass  # If no 'current' year is set, do nothing (or handle gracefully)

        # 2) Set the default month to the current month’s name, e.g. "August"
        current_month_str = timezone.now().strftime('%B')  # e.g. "August"
        # Ensure that the current month is actually in MONTH_CHOICES
        valid_months = [m[0] for m in self.fields['month'].choices]
        if current_month_str in valid_months:
            self.fields['month'].initial = current_month_str

    class Meta:
        model = PastorReport
        fields = [
            'month',
            'year',
            'number_of_evangelists',
            'number_of_local_congregations',
            'local_congregations_lords_table',
            'baptized_male',
            'baptized_female',
            'returned_male',
            'returned_female',
            'marriages_solemnized',
            'membership_transfer_sessions_count',
            'membership_transfer_sessions_where',
            'number_of_christians',
            'number_of_cell_groups',
            'church_projects',
            'number_of_joined_christians',
            'number_of_deceased_christians',
            'number_of_separated_christians',
            'number_of_relocated_christians',
            'average_income_this_month',
            'number_of_schools',
            'parish_meetings',
            'growth_explanations',
        ]
        widgets = {
            'month': forms.Select(attrs={
                'class': 'ios-select',
            }),
            'year': forms.Select(attrs={
                'class': 'ios-select',
            }),
            'number_of_evangelists': forms.NumberInput(attrs={
                'class': 'ios-input',
                'placeholder': 'Enter number of evangelists'
            }),
            'number_of_local_congregations': forms.NumberInput(attrs={
                'class': 'ios-input',
            }),
            'local_congregations_lords_table': forms.NumberInput(attrs={
                'class': 'ios-input',
            }),
            'baptized_male': forms.NumberInput(attrs={
                'class': 'ios-input',
            }),
            'baptized_female': forms.NumberInput(attrs={
                'class': 'ios-input',
            }),
            'returned_male': forms.NumberInput(attrs={
                'class': 'ios-input',
            }),
            'returned_female': forms.NumberInput(attrs={
                'class': 'ios-input',
            }),
            'marriages_solemnized': forms.NumberInput(attrs={
                'class': 'ios-input',
            }),
            'membership_transfer_sessions_count': forms.NumberInput(attrs={
                'class': 'ios-input',
            }),
            'membership_transfer_sessions_where': forms.Textarea(attrs={
                'class': 'ios-textarea',
                'rows': 3,
            }),
            'number_of_christians': forms.NumberInput(attrs={
                'class': 'ios-input',
            }),
            'number_of_cell_groups': forms.NumberInput(attrs={
                'class': 'ios-input',
            }),
            'church_projects': forms.Textarea(attrs={
                'class': 'ios-textarea',
                'rows': 3,
            }),
            'number_of_joined_christians': forms.NumberInput(attrs={
                'class': 'ios-input',
            }),
            'number_of_deceased_christians': forms.NumberInput(attrs={
                'class': 'ios-input',
            }),
            'number_of_separated_christians': forms.NumberInput(attrs={
                'class': 'ios-input',
            }),
            'number_of_relocated_christians': forms.NumberInput(attrs={
                'class': 'ios-input',
            }),
            'average_income_this_month': forms.NumberInput(attrs={
                'class': 'ios-input',
                'step': '0.01',  # For decimal input
            }),
            'number_of_schools': forms.NumberInput(attrs={
                'class': 'ios-input',
            }),
            'parish_meetings': forms.Textarea(attrs={
                'class': 'ios-textarea',
                'rows': 3,
            }),
            'growth_explanations': forms.Textarea(attrs={
                'class': 'ios-textarea',
                'rows': 4,
            }),
        }

class DatesOfServicesForm(forms.ModelForm):
    """
    Simple form for entering/editing one DatesOfServices entry.
    """
    class Meta:
        model = DatesOfServices
        fields = ['service_date']
        widgets = {
            'service_date': forms.DateInput(
                attrs={
                    'type': 'date',
                    'class': 'ios-date',
                }
            ),
        }

class VisitedLocalCongregationForm(forms.ModelForm):
    """
    Simple form for entering/editing one VisitedLocalCongregation entry.
    """
    class Meta:
        model = VisitedLocalCongregation
        fields = ['congregation_name']
        widgets = {
            'congregation_name': forms.TextInput(
                attrs={
                    'class': 'ios-input',
                    'placeholder': 'Enter congregation name',
                }
            ),
        }


# Inline formsets for the child models
DatesOfServicesFormSet = inlineformset_factory(
    PastorReport,
    DatesOfServices,
    form=DatesOfServicesForm,
    extra=1,
    can_delete=True
)

VisitedLocalCongregationFormSet = inlineformset_factory(
    PastorReport,
    VisitedLocalCongregation,
    form=VisitedLocalCongregationForm,
    extra=1,
    can_delete=True
)
