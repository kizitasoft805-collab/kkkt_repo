from django import forms
from settings.models import Cell
from .models import ChurchMember

class ChurchMemberForm(forms.ModelForm):
    class Meta:
        model = ChurchMember
        exclude = ['passport', 'member_id']
        fields = [
            'full_name', 'date_of_birth', 'gender', 'phone_number', 'email', 'address',
            'cell', 'status',
            'is_baptised', 'date_of_baptism', 'baptism_certificate',  # Baptism fields in order
            'is_confirmed', 'date_confirmed', 'confirmation_certificate',
            'marital_status', 'date_of_marriage',
            'emergency_contact_name', 'emergency_contact_phone',
            'is_this_church_member_a_leader',  # Moved to last
        ]

        widgets = {
            'full_name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': '👤 Enter Full Name',
                'style': 'border-radius: 50px; padding: 10px;',
            }),
            'date_of_birth': forms.DateInput(attrs={
                'class': 'form-control',
                'type': 'date',
                'style': 'border-radius: 50px; padding: 10px;',
            }),
            'gender': forms.Select(attrs={
                'class': 'form-control',
                'style': 'border-radius: 50px; padding: 10px;',
            }),
            'phone_number': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': '📞 255XXXXXXXXX',
                'style': 'border-radius: 50px; padding: 10px;',
            }),
            'email': forms.EmailInput(attrs={
                'class': 'form-control',
                'placeholder': '📧 Enter Gmail Address',
                'style': 'border-radius: 50px; padding: 10px;',
            }),
            'address': forms.Textarea(attrs={
                'class': 'form-control',
                'placeholder': '🏠 Enter Full Address',
                'rows': 2,
                'style': 'border-radius: 15px; padding: 10px;',
            }),
            'cell': forms.Select(attrs={
                'class': 'form-control',
                'style': 'border-radius: 50px; padding: 10px;',
            }),
            'status': forms.Select(attrs={
                'class': 'form-control',
                'style': 'border-radius: 50px; padding: 10px;',
            }),
            'is_baptised': forms.CheckboxInput(attrs={
                'class': 'form-check-input',
                'style': 'width: 20px; height: 20px;',
            }),
            'date_of_baptism': forms.DateInput(attrs={
                'class': 'form-control',
                'type': 'date',
                'style': 'border-radius: 50px; padding: 10px;',
            }),
            'baptism_certificate': forms.ClearableFileInput(attrs={
                'class': 'form-control',
                'style': 'border-radius: 15px; padding: 10px;',
            }),
            'is_confirmed': forms.CheckboxInput(attrs={
                'class': 'form-check-input',
                'style': 'width: 20px; height: 20px;',
            }),
            'date_confirmed': forms.DateInput(attrs={
                'class': 'form-control',
                'type': 'date',
                'style': 'border-radius: 50px; padding: 10px;',
            }),
            'confirmation_certificate': forms.ClearableFileInput(attrs={
                'class': 'form-control',
                'style': 'border-radius: 15px; padding: 10px;',
            }),
            'marital_status': forms.Select(attrs={
                'class': 'form-control',
                'style': 'border-radius: 50px; padding: 10px;',
            }),
            'date_of_marriage': forms.DateInput(attrs={
                'class': 'form-control',
                'type': 'date',
                'style': 'border-radius: 50px; padding: 10px;',
            }),
            'emergency_contact_name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': '📛 Emergency Contact Name',
                'style': 'border-radius: 50px; padding: 10px;',
            }),
            'emergency_contact_phone': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': '📞 255XXXXXXXXX',
                'style': 'border-radius: 50px; padding: 10px;',
            }),
            'is_this_church_member_a_leader': forms.CheckboxInput(attrs={
                'class': 'form-check-input',
                'style': 'width: 20px; height: 20px;',
            }),
        }

        labels = {
            'date_of_birth': '🎂 Date of Birth',
            'gender': '⚥ Gender',
            'cell': '🌍 Cell (Jumuiya)',
            'status': '🔵 Status',
            'is_baptised': '🌊 Baptized',
            'date_of_baptism': '🌊 Date of Baptism',
            'is_confirmed': '🕊️ Confirmed',
            'date_confirmed': '🕊️ Date of Confirmation',
            'is_this_church_member_a_leader': '👑 Is This Church Member a Leader?',
            'date_of_marriage': '💍 Date of Marriage',
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['phone_number'].initial = '255'
        self.fields['emergency_contact_phone'].initial = '255'
        for field_name, field in self.fields.items():
            if field.required:
                field.label_suffix = ' *'


class UpdateChurchMemberForm(forms.ModelForm):
    class Meta:
        model = ChurchMember
        exclude = ['passport', 'member_id']

        widgets = {
            'full_name': forms.TextInput(attrs={
                'class': 'custom-input',
                'placeholder': '👤 Enter Full Name',
            }),
            'date_of_birth': forms.DateInput(attrs={
                'class': 'custom-input',
                'type': 'date',
            }),
            'gender': forms.Select(attrs={
                'class': 'custom-input',
            }),
            'phone_number': forms.TextInput(attrs={
                'class': 'custom-input',
                'placeholder': '📞 255XXXXXXXXX',
            }),
            'email': forms.EmailInput(attrs={
                'class': 'custom-input',
                'placeholder': '📧 Enter Gmail Address',
            }),
            'address': forms.Textarea(attrs={
                'class': 'custom-textarea',
                'placeholder': '🏠 Enter Full Address',
                'rows': 2,
            }),

            # 🌍 Cell Field
            'cell': forms.Select(attrs={
                'class': 'custom-input',
            }),

            # 🔵 Status Field (Active/Inactive)
            'status': forms.Select(attrs={
                'class': 'custom-input',
            }),

            # Baptism Fields
            'is_baptised': forms.CheckboxInput(attrs={
                'class': 'custom-checkbox',
            }),
            'date_of_baptism': forms.DateInput(attrs={
                'class': 'custom-input',
                'type': 'date',
            }),
            'baptism_certificate': forms.ClearableFileInput(attrs={
                'class': 'custom-file',
            }),

            # Confirmation Fields
            'date_confirmed': forms.DateInput(attrs={
                'class': 'custom-input',
                'type': 'date',
            }),
            'confirmation_certificate': forms.ClearableFileInput(attrs={
                'class': 'custom-file',
            }),

            # Marriage Fields
            'marital_status': forms.Select(attrs={
                'class': 'custom-input',
            }),
            'date_of_marriage': forms.DateInput(attrs={
                'class': 'custom-input',
                'type': 'date',
            }),

            # Emergency Contact
            'emergency_contact_name': forms.TextInput(attrs={
                'class': 'custom-input',
                'placeholder': '📛 Emergency Contact Name',
            }),
            'emergency_contact_phone': forms.TextInput(attrs={
                'class': 'custom-input',
                'placeholder': '📞 255XXXXXXXXX',
            }),
        }

        labels = {
            'date_of_birth': '🎂 Date of Birth',
            'gender': '⚥ Gender',
            'cell': '🌍 Cell (Jumuiya)',
            'status': '🔵 Status',
            'is_baptised': '🌊 Baptized',
            'date_of_baptism': '🌊 Date of Baptism',
            'date_confirmed': '🕊️ Date of Confirmation',
            'date_of_marriage': '💍 Date of Marriage',
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Changed initial values from +255 to 255
        self.fields['phone_number'].initial = '255'
        self.fields['emergency_contact_phone'].initial = '255'

        # Add * for required fields
        for field_name, field in self.fields.items():
            if field.required:
                field.label_suffix = ' *'

class ChurchMemberPassportForm(forms.ModelForm):
    class Meta:
        model = ChurchMember
        fields = ['passport']
        widgets = {
            'passport': forms.ClearableFileInput(attrs={
                'class': 'form-control',
                'style': (
                    'border-radius: 50px; '
                    'padding: 15px; '
                    'width: 100%; '
                    'box-sizing: border-box; '
                    'border: 1px solid #ccc; '
                    'background-color: #f9f9f9; '
                    'font-size: 16px; '
                    'outline: none; '
                ),
            }),
        }
        labels = {
            'passport': '🖼️ Upload Passport',
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['passport'].widget.attrs.update({
            'title': 'Choose a passport file',
        })




from django import forms
from .models import ChurchMember
from settings.models import Cell

class ChurchMemberSignupForm(forms.ModelForm):
    class Meta:
        model = ChurchMember
        fields = [
            'full_name', 'date_of_birth', 'gender', 'phone_number', 'email', 'address', 'cell',
            'is_baptised', 'date_of_baptism', 'baptism_certificate', 'is_confirmed', 'date_confirmed',
            'confirmation_certificate', 'marital_status', 'date_of_marriage', 'emergency_contact_name',
            'emergency_contact_phone', 'passport'
        ]
        widgets = {
            'full_name': forms.TextInput(attrs={'class': 'iphone-field', 'placeholder': 'e.g., John Middle Doe'}),
            'date_of_birth': forms.DateInput(attrs={'class': 'iphone-field', 'type': 'date', 'placeholder': 'Select your date of birth'}),
            'gender': forms.Select(attrs={'class': 'iphone-field', 'placeholder': 'Select your gender'}),
            'phone_number': forms.TextInput(attrs={'class': 'iphone-field', 'placeholder': 'e.g., 255712345678', 'value': '255'}),
            'email': forms.EmailInput(attrs={'class': 'iphone-field', 'placeholder': 'e.g., john.doe@gmail.com'}),
            'address': forms.Textarea(attrs={'class': 'iphone-field', 'rows': 3, 'placeholder': 'e.g., 123 Church St, Dar es Salaam'}),
            'cell': forms.Select(attrs={'class': 'iphone-field', 'placeholder': 'Select your cell'}),
            'date_of_baptism': forms.DateInput(attrs={'class': 'iphone-field', 'type': 'date', 'placeholder': 'Select baptism date (if applicable)'}),
            'baptism_certificate': forms.FileInput(attrs={'class': 'iphone-field', 'placeholder': 'Upload your baptism certificate (PDF/JPG)'}),
            'date_confirmed': forms.DateInput(attrs={'class': 'iphone-field', 'type': 'date', 'placeholder': 'Select confirmation date (if applicable)'}),
            'confirmation_certificate': forms.FileInput(attrs={'class': 'iphone-field', 'placeholder': 'Upload your confirmation certificate (PDF/JPG)'}),
            'marital_status': forms.Select(attrs={'class': 'iphone-field', 'placeholder': 'Select your marital status'}),
            'date_of_marriage': forms.DateInput(attrs={'class': 'iphone-field', 'type': 'date', 'placeholder': 'Select marriage date (if applicable)'}),
            'emergency_contact_name': forms.TextInput(attrs={'class': 'iphone-field', 'placeholder': 'e.g., Jane Middle Doe'}),
            'emergency_contact_phone': forms.TextInput(attrs={'class': 'iphone-field', 'placeholder': 'e.g., 255798765432', 'value': '255'}),
            'passport': forms.FileInput(attrs={'class': 'iphone-field', 'placeholder': 'Upload your passport photo (JPG/PNG)'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['is_baptised'].label = 'Are you baptized?'
        self.fields['is_confirmed'].label = 'Are you confirmed?'

    def clean_phone_number(self):
        phone_number = self.cleaned_data['phone_number']
        if not phone_number.startswith('255'):
            raise forms.ValidationError("Phone number must start with '255'.")
        return phone_number

    def clean_emergency_contact_phone(self):
        emergency_contact_phone = self.cleaned_data['emergency_contact_phone']
        if not emergency_contact_phone.startswith('255'):
            raise forms.ValidationError("Emergency contact phone number must start with '255'.")
        return emergency_contact_phone