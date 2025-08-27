from django import forms
from .models import Offerings
from django.utils.timezone import now
from members.models import ChurchMember
from leaders.models import Leader  # Import Leader model
from settings.models import OutStation  # Import OutStation model

class OfferingsForm(forms.ModelForm):
    """
    Form for creating an offering entry.
    """

    class Meta:
        model = Offerings
        fields = ['date_given', 'service_time', 'amount', 'collected_by', 'recorded_by', 'mass_name', 'notes', 'outstation']
        widgets = {
            # 📅 Date Given (Default Today)
            'date_given': forms.DateInput(
                attrs={
                    'class': 'form-control',
                    'type': 'date',
                    'value': now().strftime('%Y-%m-%d'),  # Default date to today
                    'style': 'border-radius: 50px; padding: 10px;',
                }
            ),

            # ⏰ Service Time (Dropdown)
            'service_time': forms.Select(
                attrs={
                    'class': 'form-control',
                    'style': 'border-radius: 50px; padding: 10px;',
                }
            ),

            # 💰 Amount Input
            'amount': forms.NumberInput(
                attrs={
                    'class': 'form-control',
                    'placeholder': 'Enter amount collected...',
                    'style': 'border-radius: 50px; padding: 10px;',
                }
            ),

            # 📖 Mass Name Input
            'mass_name': forms.TextInput(
                attrs={
                    'class': 'form-control',
                    'placeholder': 'Enter mass name...',
                    'style': 'border-radius: 50px; padding: 10px;',
                }
            ),

            # 🗒️ Notes Textarea
            'notes': forms.Textarea(
                attrs={
                    'class': 'form-control',
                    'placeholder': 'Additional notes (optional)...',
                    'rows': 3,
                    'style': 'border-radius: 15px; padding: 10px;',
                }
            ),

            # 🏛️ Outstation (Dropdown)
            'outstation': forms.Select(
                attrs={
                    'class': 'form-control',
                    'style': 'border-radius: 50px; padding: 10px;',
                }
            ),
        }

    def __init__(self, *args, **kwargs):
        """
        Custom initialization for dynamically loading church members and outstations in choices.
        - "Collected By" will contain all active members with ✅.
        - "Recorded By" will contain only leaders who are active with ✅.
        - "Outstation" will contain all outstations.
        """
        super().__init__(*args, **kwargs)

        # Load active church members into "Collected By" dropdown with ✅
        active_members = ChurchMember.objects.filter(status="Active")
        self.fields['collected_by'].choices = [("", "Select collector...")] + [
            (member.pk, f"✅ {member.full_name}") for member in active_members
        ]

        # Load only active leaders into "Recorded By" dropdown with ✅
        active_leaders = ChurchMember.objects.filter(leader__isnull=False, status="Active")
        self.fields['recorded_by'].choices = [("", "Select recorder (Leader Only)...")] + [
            (leader.pk, f"✅ {leader.full_name}") for leader in active_leaders
        ]

        # Load all outstations into "Outstation" dropdown
        outstations = OutStation.objects.all()
        self.fields['outstation'].choices = [("", "Select outstation...")] + [
            (outstation.pk, f"{outstation.name} - {outstation.location}") for outstation in outstations
        ]

        # Apply styles to dropdown fields
        for field_name in ['collected_by', 'recorded_by', 'outstation']:
            self.fields[field_name].widget.attrs.update({
                'class': 'form-control',
                'style': 'border-radius: 50px; padding: 10px;',
            })

from django import forms
from .models import FacilityRenting
from properties.models import ChurchAsset

class FacilityRentingForm(forms.ModelForm):
    class Meta:
        model = FacilityRenting
        fields = ['property_rented', 'rentor_name', 'amount', 'date_rented', 'end_date', 'purpose']  # ✅ Added 'end_date'

        # 🌟 Base Styles for All Fields
        base_style = 'padding: 14px; border-radius: 15px; border: 1px solid #ccc; width: 100%; box-sizing: border-box;'

        widgets = {
            'property_rented': forms.Select(attrs={
                'class': 'form-control iphone-style',
                'placeholder': '🏠 Select Property',
                'style': base_style,
            }),
            'rentor_name': forms.TextInput(attrs={
                'class': 'form-control iphone-style',
                'placeholder': "👤 Enter Rentor's Name",
                'style': base_style,
            }),
            'amount': forms.NumberInput(attrs={
                'class': 'form-control iphone-style',
                'placeholder': '💰 Enter Amount (TZS)',
                'style': base_style,
                'min': '0',
                'step': '0.01',
            }),
            'date_rented': forms.DateInput(attrs={
                'type': 'date',
                'class': 'form-control iphone-style',
                'placeholder': '📆 Select Rental Date',
                'style': base_style,
            }),
            'end_date': forms.DateInput(attrs={  # ✅ Added End Date Field
                'type': 'date',
                'class': 'form-control iphone-style',
                'placeholder': '📅 Select End Date',
                'style': base_style,
            }),
            'purpose': forms.Textarea(attrs={
                'class': 'form-control iphone-style',
                'placeholder': '🎯 Enter Purpose for Renting',
                'style': base_style + ' height: 100px; resize: none;',
                'rows': 4,
            }),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # ✅ Filter allowed church assets
        allowed_asset_types = ['Building', 'Electronics', 'Equipment', 'Vehicle']
        self.fields['property_rented'].queryset = ChurchAsset.objects.filter(
            asset_type__in=allowed_asset_types
        )

        # ✅ Labels and Help Texts
        self.fields['property_rented'].label = "🏠 Select Property"
        self.fields['property_rented'].help_text = "Choose the property to be rented"

        self.fields['rentor_name'].label = "👤 Rentor's Name"
        self.fields['rentor_name'].help_text = "Enter the full name of the person renting"

        self.fields['amount'].label = "💰 Amount (TZS)"
        self.fields['amount'].help_text = "Enter the rental amount in Tanzanian Shillings"

        self.fields['date_rented'].label = "📆 Rental Date"
        self.fields['date_rented'].help_text = "Select the date of renting"

        # 🎯 Purpose Field Label & Help Text
        self.fields['purpose'].label = "🎯 Purpose of Renting"
        self.fields['purpose'].help_text = "Briefly describe the purpose of renting the facility"

        # 📅 End Date Field Label & Help Text
        self.fields['end_date'].label = "📅 Rental End Date"
        self.fields['end_date'].help_text = "Specify the date when the rental will end"


from django import forms
from .models import SpecialContribution

class SpecialContributionForm(forms.ModelForm):
    class Meta:
        model = SpecialContribution
        fields = ['contribution_type', 'name', 'description']

        # 🎨 Styling with Inline CSS for iPhone-like Design
        base_style = (
            'padding: 14px; '
            'border-radius: 15px; '
            'border: 1px solid #ccc; '
            'width: 100%; '
            'box-sizing: border-box;'
        )

        widgets = {
            'contribution_type': forms.Select(attrs={
                'class': 'form-control iphone-style',
                'style': base_style,
            }),
            'name': forms.TextInput(attrs={
                'class': 'form-control iphone-style',
                'placeholder': '🏷️ Enter Contribution Name',
                'style': base_style,
            }),
            'description': forms.Textarea(attrs={
                'class': 'form-control iphone-style',
                'placeholder': '📝 Enter Contribution Description',
                'style': base_style + ' height: 100px; resize: none;',
                'rows': 4,
            }),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Field labels
        self.fields['contribution_type'].label = "Select Contribution Type"
        self.fields['name'].label = "🏷️ Contribution Name"
        self.fields['description'].label = "📝 Description"

from django import forms
from .models import DonationItemFund

class DonationItemFundForm(forms.ModelForm):
    class Meta:
        model = DonationItemFund
        fields = ['period', 'mass_name', 'amount', 'notes']  # ✅ Added 'amount'

        # 🌟 Stylish Widgets
        widgets = {
            'period': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': '📅 Enter Period (e.g., Q1 2024, January 2024)',
                'style': 'padding: 12px; border-radius: 8px; border: 1px solid #ccc;'
            }),
            'mass_name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': '⛪ Enter Mass Name',
                'style': 'padding: 12px; border-radius: 8px; border: 1px solid #ccc;'
            }),
            'amount': forms.NumberInput(attrs={  # ✅ Amount Field Styling
                'class': 'form-control',
                'placeholder': '💰 Enter Amount Obtained',
                'style': 'padding: 12px; border-radius: 8px; border: 1px solid #ccc;',
                'min': '0',
                'step': '0.01'
            }),
            'notes': forms.Textarea(attrs={
                'class': 'form-control',
                'placeholder': '📝 Enter Notes (optional)',
                'style': 'padding: 12px; border-radius: 8px; border: 1px solid #ccc; height: 100px;',
                'rows': 4,
            }),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Optional: Add custom labels
        self.fields['amount'].label = "💰 Amount Obtained"


import datetime
from django import forms
from django.utils.timezone import now
from .models import Pledge
from members.models import ChurchMember
from settings.models import Year


class PledgeForm(forms.ModelForm):
    """
    A decorated form for recording pledges with custom widgets and emoji placeholders.
    """

    # Months Choices
    MONTH_CHOICES = [
        ('January', 'January'), ('February', 'February'), ('March', 'March'),
        ('April', 'April'), ('May', 'May'), ('June', 'June'),
        ('July', 'July'), ('August', 'August'), ('September', 'September'),
        ('October', 'October'), ('November', 'November'), ('December', 'December')
    ]

    member = forms.ModelChoiceField(
        queryset=ChurchMember.objects.filter(status='Active'),
        widget=forms.Select(attrs={'class': 'form-control'}),
        help_text="Select the church member making the pledge."
    )
    year = forms.ModelChoiceField(
        queryset=Year.objects.all(),
        widget=forms.Select(attrs={'class': 'form-control'}),
        help_text="The year in which the pledge is being made."
    )
    month = forms.ChoiceField(
        choices=MONTH_CHOICES,
        widget=forms.Select(attrs={'class': 'form-control'}),
        help_text="The month in which the pledge is made."
    )
    date_given = forms.DateField(
        widget=forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
        help_text="Select the date when the pledge was given."
    )
    envelope_number = forms.CharField(
        max_length=50,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': '📩 Enter Envelope Number'
        }),
        help_text="The envelope number used for the pledge."
    )
    pledge_amount = forms.DecimalField(
        max_digits=10,
        decimal_places=2,
        widget=forms.NumberInput(attrs={
            'class': 'form-control',
            'placeholder': '💰 Enter Pledge Amount'
        }),
        help_text="Enter the amount pledged."
    )
    pledge_for_construction = forms.DecimalField(
        max_digits=10,
        decimal_places=2,
        widget=forms.NumberInput(attrs={
            'class': 'form-control',
            'placeholder': '🏗️ Enter Pledge for Construction'
        }),
        help_text="Enter the amount pledged for construction."
    )

    class Meta:
        model = Pledge
        fields = [
            'member', 'year', 'month', 'date_given',
            'envelope_number', 'pledge_amount', 'pledge_for_construction'
        ]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # 1) Set default year to the Year object where is_current=True
        current_year_obj = Year.objects.filter(is_current=True).first()
        if current_year_obj:
            self.fields['year'].initial = current_year_obj

        # 2) Default month = current month name (e.g. "February")
        self.fields['month'].initial = now().strftime('%B')

        # 3) Default date = today's date
        self.fields['date_given'].initial = now().date()

        # 4) Only active members in the dropdown
        self.fields['member'].queryset = ChurchMember.objects.filter(status='Active')

        # 5) Customize label display for member dropdown
        self.fields['member'].label_from_instance = (
            lambda obj: f"✅ {obj.full_name} - 📞 {obj.phone_number} - 🏠 {obj.address}"
        )

from django import forms
from .models import Category

class CategoryForm(forms.ModelForm):
    """
    Form for creating or updating Category.
    """
    class Meta:
        model = Category
        fields = ['name', 'description']

        # Example iPhone-like styling
        base_style = (
            'padding: 14px; '
            'border-radius: 15px; '
            'border: 1px solid #ccc; '
            'width: 100%; '
            'box-sizing: border-box; '
            'font-size: 16px;'
        )

        widgets = {
            'name': forms.TextInput(attrs={
                'placeholder': 'Category Name',
                'style': base_style + ' margin-bottom: 10px;',
            }),
            'description': forms.Textarea(attrs={
                'placeholder': 'Brief description...',
                'style': base_style + ' height: 100px; resize: none;',
                'rows': 4,
            }),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['name'].label = "Category Name"
        self.fields['description'].label = "Description"


# finance/forms.py

from django import forms
from django.utils.timezone import now
from .models import Expenditure
from settings.models import Year

class ExpenditureForm(forms.ModelForm):
    """
    Form for creating/updating an Expenditure,
    EXCLUDING the category field (assigned in the view),
    BUT including:
      - expenditure_purpose (as the first field)
      - notes (as the last field)
      - year, month, date_taken, expenditure_amount, receipt
    """

    class Meta:
        model = Expenditure
        # NEW ORDER: Put expenditure_purpose FIRST, notes LAST
        fields = [
            'expenditure_purpose',   # 1st
            'year', 
            'month', 
            'date_taken', 
            'expenditure_amount', 
            'receipt',
            'notes'                 # Last
        ]

        base_style = (
            'padding: 14px; '
            'border-radius: 15px; '
            'border: 1px solid #ccc; '
            'width: 100%; '
            'box-sizing: border-box; '
            'font-size: 16px;'
        )

        widgets = {
            'expenditure_purpose': forms.TextInput(attrs={
                'placeholder': 'Enter a short purpose for this expenditure',
                'style': base_style,
            }),
            'year': forms.Select(attrs={
                'style': base_style,
            }),
            'month': forms.Select(attrs={
                'style': base_style,
            }),
            'date_taken': forms.DateTimeInput(attrs={
                'type': 'datetime-local',
                'style': base_style,
            }),
            'expenditure_amount': forms.NumberInput(attrs={
                'placeholder': 'Enter the expenditure amount',
                'style': base_style,
            }),
            'receipt': forms.ClearableFileInput(attrs={
                'style': base_style,
            }),
            'notes': forms.Textarea(attrs={
                'placeholder': 'Additional notes or remarks',
                'rows': 4,
                'style': base_style + ' height: 100px; resize: none;',
            }),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # Only set defaults if creating a new record
        if not self.instance.pk:
            # Default Year => the 'Year' with is_current=True
            try:
                current_year = Year.objects.get(is_current=True)
                self.fields['year'].initial = current_year
            except Year.DoesNotExist:
                pass

            # Default Month => system's current month name
            current_month = now().strftime("%B")  # e.g. "August"
            self.fields['month'].initial = current_month

        # Field labels
        self.fields['expenditure_purpose'].label = "Purpose"
        self.fields['year'].label = "Year"
        self.fields['month'].label = "Month"
        self.fields['date_taken'].label = "Date Taken"
        self.fields['expenditure_amount'].label = "Expenditure Amount"
        self.fields['receipt'].label = "Receipt Document"
        self.fields['notes'].label = "Notes"

# finance/forms.py

from django import forms
from .models import OfferingCategory

class OfferingCategoryForm(forms.ModelForm):
    """
    Form for creating or updating an OfferingCategory.
    """
    class Meta:
        model = OfferingCategory
        fields = ['name', 'description']

        base_style = (
            'padding: 14px; '
            'border-radius: 15px; '
            'border: 1px solid #ccc; '
            'font-size: 16px; '
            'width: 100%; '
            'box-sizing: border-box; '
            'outline: none;'
        )

        widgets = {
            'name': forms.TextInput(attrs={
                'style': base_style,
                'placeholder': 'Enter category name',
                'class': 'iphone-input'
            }),
            'description': forms.Textarea(attrs={
                'style': base_style + ' height: 100px; resize: none;',
                'placeholder': 'Optional description...',
                'class': 'iphone-input'
            }),
        }

