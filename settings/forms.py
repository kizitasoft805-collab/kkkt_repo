# settings/forms.py

from django import forms
from .models import Year, OutStation, Cell, ChurchLocation  # Updated imports

class YearForm(forms.ModelForm):
    class Meta:
        model = Year
        fields = ['year', 'is_current']
        widgets = {
            'year': forms.Select(attrs={
                'class': 'form-control',
                'style': (
                    'border-radius: 10px; '          # Rounded corners
                    'padding: 12px; '               # Padding for a better touch target
                    'width: 100%; '                 # Full width for responsive design
                    'max-width: 600px; '            # Optional maximum width for larger viewports
                    'box-sizing: border-box; '      # Ensure padding is included in the width
                ),
            }),
            'is_current': forms.CheckboxInput(attrs={
                'class': 'form-check-input',
                'style': (
                    'transform: scale(1.2); '       # Slightly larger checkbox
                    'margin-top: 10px; '            # Add spacing above checkbox
                ),
            }),
        }
        labels = {
            'year': 'Select Year',
            'is_current': 'Set as Current Year',
        }

class OutStationForm(forms.ModelForm):  # Changed from ZoneForm
    """
    Form to create or update a church outstation with iPhone-like styling.
    """
    class Meta:
        model = OutStation  # Changed from Zone
        fields = ['name', 'description', 'location']
        widgets = {
            'name': forms.TextInput(attrs={
                'class': 'custom-input',
                'placeholder': '🏡 Enter Outstation Name',  # Updated placeholder
                'autocomplete': 'off',
            }),
            'description': forms.Textarea(attrs={
                'class': 'custom-textarea',
                'placeholder': '📝 Enter Description',
                'rows': 3,
            }),
            'location': forms.TextInput(attrs={
                'class': 'custom-input',
                'placeholder': '📍 Enter Location',
                'autocomplete': 'off',
            }),
        }

class CellForm(forms.ModelForm):  # Changed from CommunityForm
    """
    Form to create or update a church cell with iPhone-like styling.
    """
    class Meta:
        model = Cell  # Changed from Community
        fields = ['name', 'outstation', 'location', 'description']  # Changed 'zone' to 'outstation'
        widgets = {
            'name': forms.TextInput(attrs={
                'class': 'custom-input',
                'placeholder': '🏷️ Enter Cell Name',  # Updated placeholder
                'autocomplete': 'off',
            }),
            'outstation': forms.Select(attrs={  # Changed from 'zone' to 'outstation'
                'class': 'custom-input',
                'placeholder': '📍 Select Outstation',  # Updated placeholder
            }),
            'location': forms.TextInput(attrs={
                'class': 'custom-input',
                'placeholder': '📍 Enter Cell Location',  # Updated placeholder
                'autocomplete': 'off',
            }),
            'description': forms.Textarea(attrs={
                'class': 'custom-textarea',
                'placeholder': '📝 Enter Description',
                'rows': 3,
            }),
        }

class ChurchLocationForm(forms.ModelForm):
    """
    Form for entering church location manually or via map selection.
    """
    latitude = forms.FloatField(
        widget=forms.TextInput(attrs={
            'placeholder': '📍 Enter Latitude',
            'style': 'width: 100%; padding: 12px; border-radius: 25px; text-align: center;'
        })
    )
    longitude = forms.FloatField(
        widget=forms.TextInput(attrs={
            'placeholder': '📍 Enter Longitude',
            'style': 'width: 100%; padding: 12px; border-radius: 25px; text-align: center;'
        })
    )

    class Meta:
        model = ChurchLocation
        fields = ['latitude', 'longitude']