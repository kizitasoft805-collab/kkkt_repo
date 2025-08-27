# leaders/forms.py
from django import forms
from .models import Leader, ChurchMember
from settings.models import OutStation  # Import OutStation for queryset

class LeaderForm(forms.ModelForm):
    class Meta:
        model = Leader
        exclude = ['time_in_service', 'leader_id']  # Excluding 'time_in_service' since it is calculated automatically
        widgets = {
            # Select Church Member
            'church_member': forms.Select(attrs={
                'class': 'form-control',
                'style': 'border-radius: 25px; padding: 10px; width: 100%;',
            }),

            # Occupation
            'occupation': forms.Select(attrs={
                'class': 'form-control',
                'style': 'border-radius: 25px; padding: 10px; width: 100%;',
            }),

            # Start Date
            'start_date': forms.DateInput(attrs={
                'class': 'form-control',
                'type': 'date',
                'style': 'border-radius: 25px; padding: 10px; width: 100%;',
            }),

            # Responsibilities
            'responsibilities': forms.Textarea(attrs={
                'class': 'form-control',
                'placeholder': '📋 Enter responsibilities',
                'rows': 3,
                'style': 'border-radius: 25px; padding: 10px; width: 100%;',
            }),

            # Outstation
            'outstation': forms.Select(attrs={
                'class': 'form-control',
                'style': 'border-radius: 25px; padding: 10px; width: 100%;',
                'id': 'id_outstation'  # Explicit ID for JavaScript
            }),
        }
        labels = {
            'church_member': '👤 Select Church Member *',
            'occupation': '🛠 Occupation *',
            'start_date': '📅 Start Date *',
            'responsibilities': '📋 Responsibilities *',
            'outstation': '🏠 Outstation *',  # Label with * (required for Evangelist enforced in model)
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # Set choices for church members dynamically
        self.fields['church_member'].queryset = ChurchMember.objects.all()
        self.fields['church_member'].label_from_instance = lambda obj: f"{obj.full_name} ({obj.phone_number})"

        # Set choices for outstation dynamically
        self.fields['outstation'].queryset = OutStation.objects.all()

        # Add * to required field labels
        for field_name, field in self.fields.items():
            if field.required:
                field.label_suffix = ' *'  # Appends * to required fields