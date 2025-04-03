from django import forms
from django.forms import formset_factory
from .models import ChurchAsset

class ChurchAssetForm(forms.ModelForm):
    """
    Form to create a church asset with an iPhone-like design.
    """

    class Meta:
        model = ChurchAsset
        fields = [
            'name', 'asset_type', 'description', 'acquisition_date',
            'quantity_name', 'quantity', 'status', 'value'
        ]
        widgets = {
            'name': forms.TextInput(attrs={
                'class': 'form-control rounded-input uniform-field', 
                'placeholder': '🏛️ Enter Asset Name',
                'autocomplete': 'off'
            }),
            'asset_type': forms.Select(attrs={
                'class': 'form-control rounded-input uniform-field'
            }),
            'description': forms.Textarea(attrs={
                'class': 'form-control rounded-input uniform-field', 
                'rows': 3, 
                'placeholder': '📝 Brief Description...'
            }),
            'acquisition_date': forms.DateInput(attrs={
                'class': 'form-control rounded-input uniform-field', 
                'type': 'date'
            }),
            'quantity_name': forms.Select(attrs={
                'class': 'form-control rounded-input uniform-field'
            }),
            'quantity': forms.NumberInput(attrs={
                'class': 'form-control rounded-input uniform-field', 
                'placeholder': '🔢 Quantity'
            }),
            'status': forms.Select(attrs={
                'class': 'form-control rounded-input uniform-field'
            }),
            'value': forms.NumberInput(attrs={
                'class': 'form-control rounded-input uniform-field', 
                'placeholder': '💰 Estimated Value (Currency)'
            }),
        }
        labels = {
            'acquisition_date': '📅 Acquisition Date (Optional)',
            'quantity_name': '📦 Quantity Unit',
            'value': '💰 Value (Currency)',
        }

    # Override quantity_name field to use predefined choices
    quantity_name = forms.ChoiceField(
        choices=ChurchAsset.QUANTITY_NAME_CHOICES,
        widget=forms.Select(attrs={'class': 'form-control rounded-input uniform-field'})
    )

# Create a Formset for multiple Church Assets
ChurchAssetFormSet = formset_factory(ChurchAssetForm, extra=1, can_delete=True)

from django import forms
from .models import ChurchAssetMedia

class ChurchAssetMediaForm(forms.ModelForm):
    """
    Form to upload media for a ChurchAsset.
    """
    class Meta:
        model = ChurchAssetMedia
        fields = ['image']
        widgets = {
            'image': forms.ClearableFileInput(attrs={'class': 'form-control file-input', 'multiple': False}),  
        }
        labels = {
            'image': '📸 Upload Asset Image',
        }

from django import forms
from .models import ChurchAsset

class UpdateChurchAssetForm(forms.ModelForm):
    class Meta:
        model = ChurchAsset
        fields = [
            'name', 'asset_type', 'description', 'acquisition_date',
            'quantity_name', 'quantity', 'status', 'value'
        ]

        widgets = {
            'name': forms.TextInput(attrs={
                'class': 'form-control rounded-input uniform-field', 
                'placeholder': '🏛️ Enter Asset Name',
                'autocomplete': 'off'
            }),
            'asset_type': forms.Select(attrs={
                'class': 'form-control rounded-input uniform-field'
            }),
            'description': forms.Textarea(attrs={
                'class': 'form-control rounded-input uniform-field', 
                'rows': 3, 
                'placeholder': '📝 Brief Description...'
            }),
            'acquisition_date': forms.DateInput(attrs={
                'class': 'form-control rounded-input uniform-field', 
                'type': 'date'
            }),
            'quantity_name': forms.Select(attrs={
                'class': 'form-control rounded-input uniform-field'
            }),
            'quantity': forms.NumberInput(attrs={
                'class': 'form-control rounded-input uniform-field', 
                'placeholder': '🔢 Quantity',
                'min': 1
            }),
            'status': forms.Select(attrs={
                'class': 'form-control rounded-input uniform-field'
            }),
            'value': forms.NumberInput(attrs={
                'class': 'form-control rounded-input uniform-field', 
                'placeholder': '💰 Estimated Value (Currency)',
                'step': '0.01'
            }),
        }

        labels = {
            'name': '🏛️ Asset Name',
            'asset_type': '📂 Type of Asset',
            'description': '📝 Asset Description',
            'acquisition_date': '📅 Acquisition Date',
            'quantity_name': '📦 Quantity Type',
            'quantity': '🔢 Quantity',
            'status': '🔧 Current Status',
            'value': '💰 Estimated Value (TZS)',
        }

    # Override quantity_name field to use predefined choices
    quantity_name = forms.ChoiceField(
        choices=ChurchAsset.QUANTITY_NAME_CHOICES,
        widget=forms.Select(attrs={'class': 'form-control rounded-input uniform-field'})
    )

