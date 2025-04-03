from django import forms

class LoginForm(forms.Form):
    username = forms.CharField(
        max_length=150,
        required=True,
        label="Username or Email",
        widget=forms.TextInput(attrs={
            'placeholder': 'Enter your username or email',
            'class': 'form-control',
            'style': (
                'border-radius: 999px; '
                'width: 100%; '
                'max-width: 400px; '
                # Removed "padding: 10px;" here
            ),
        })
    )

    password = forms.CharField(
        required=True,
        widget=forms.PasswordInput(attrs={
            'placeholder': 'Enter your password',
            'class': 'form-control',
            'style': (
                'border-radius: 999px; '
                'width: 100%; '
                'max-width: 400px; '
                # Removed "padding: 10px;" here
            ),
        })
    )

# accounts/forms.py

from django import forms
from .models import CustomUser

class ProfilePictureForm(forms.ModelForm):
    class Meta:
        model = CustomUser
        fields = ['profile_picture']
        widgets = {
            'profile_picture': forms.ClearableFileInput(attrs={
                'class': 'form-control',
                'style': (
                    'width: 100%; '                  # Full width for viewport
                    'max-width: 400px; '             # Optional max width for larger screens
                    'padding: 10px; '                # Add padding for better usability
                    'border-radius: 999px; '         # Fully rounded edges
                    'border: 1px solid #ccc; '       # Subtle border for visibility
                    'box-shadow: 0px 4px 6px rgba(0, 0, 0, 0.1); ' # Soft shadow for depth
                    'margin: 10px auto; '            # Center-align with auto margins
                ),
            }),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['profile_picture'].label = 'Upload Profile Picture'

from django import forms
from django.contrib.auth.forms import UserChangeForm
from django.forms.widgets import ClearableFileInput
from .models import CustomUser

class AdminUpdateForm(UserChangeForm):
    """
    Form to allow the admin to update their details with a clearable profile picture field.
    """

    profile_picture = forms.FileField(
        label="📷 Profile Picture",
        widget=ClearableFileInput(attrs={
            'class': 'form-control',
            'style': 'border-radius: 25px; padding: 10px; width: 100%;',
        }),
        required=False,
    )

    username = forms.CharField(
        label="👤 Username",
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': '👤 Enter Username',
            'style': 'border-radius: 25px; padding: 10px; width: 100%;'
        })
    )

    email = forms.EmailField(
        label="📧 Email",
        widget=forms.EmailInput(attrs={
            'class': 'form-control',
            'placeholder': '📧 Enter Email',
            'style': 'border-radius: 25px; padding: 10px; width: 100%;'
        }),
        required=False
    )

    phone_number = forms.CharField(
        label="📞 Phone Number",
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': '📞 Enter Phone Number',
            'style': 'border-radius: 25px; padding: 10px; width: 100%;'
        })
    )

    user_type = forms.ChoiceField(
        label="👔 User Type",
        choices=CustomUser.USER_TYPES,
        widget=forms.Select(attrs={
            'class': 'form-control',
            'style': 'border-radius: 25px; padding: 10px; width: 100%;'
        })
    )

    password = forms.CharField(
        label="🔑 New Password (Leave blank to keep current)",
        widget=forms.PasswordInput(attrs={
            'class': 'form-control',
            'placeholder': '🔑 Enter new password (Optional)',
            'style': 'border-radius: 25px; padding: 10px; width: 100%;'
        }),
        required=False,
    )

    confirm_password = forms.CharField(
        label="🔑 Confirm New Password",
        widget=forms.PasswordInput(attrs={
            'class': 'form-control',
            'placeholder': '🔑 Confirm new password',
            'style': 'border-radius: 25px; padding: 10px; width: 100%;'
        }),
        required=False,
    )

    class Meta:
        model = CustomUser
        fields = ['profile_picture', 'username', 'email', 'phone_number', 'user_type']
    
    def clean(self):
        """
        Custom validation to ensure passwords match if provided.
        """
        cleaned_data = super().clean()
        password = cleaned_data.get("password")
        confirm_password = cleaned_data.get("confirm_password")

        if password and password != confirm_password:
            self.add_error("confirm_password", "Passwords do not match.")

        return cleaned_data

    def save(self, commit=True):
        """
        Save the user instance and update the password if provided.
        """
        user = super().save(commit=False)
        password = self.cleaned_data.get("password")

        if password:
            user.set_password(password)

        if commit:
            user.save()
        return user

from django import forms
from .models import CustomUser
from members.models import ChurchMember

class AccountRequestForm(forms.ModelForm):
    """
    Form to request an account for Church Members.
    """
    member_id = forms.CharField(
        max_length=20,
        required=True,
        label="Member ID",
        widget=forms.TextInput(attrs={
            'placeholder': '🆔 Enter your Church Member ID',
            'style': 'width: 100%; padding: 12px; border-radius: 25px;'
        }),
    )
    
    email = forms.EmailField(
        required=False,
        widget=forms.EmailInput(attrs={
            'placeholder': '📧 Enter your email (Optional)',
        }),
    )

    username = forms.CharField(
        max_length=150,
        required=True,
        widget=forms.TextInput(attrs={
            'placeholder': '👤 Choose a username',
        }),
    )

    password = forms.CharField(
        widget=forms.PasswordInput(attrs={
            'placeholder': '🔒 Enter a strong password',
        }),
        required=True,
    )

    confirm_password = forms.CharField(
        widget=forms.PasswordInput(attrs={
            'placeholder': '🔑 Confirm your password',
        }),
        required=True,
    )

    class Meta:
        model = CustomUser
        fields = ['member_id', 'email', 'username', 'password', 'confirm_password']

    def clean_member_id(self):
        """
        Validate if the entered member ID exists in the ChurchMember model.
        """
        member_id = self.cleaned_data['member_id']
        try:
            member = ChurchMember.objects.get(member_id=member_id)
            return member
        except ChurchMember.DoesNotExist:
            raise forms.ValidationError("❌ The system does not identify you. Please contact the admin at +255767972343.")

    def clean(self):
        """
        Custom validation for password confirmation.
        """
        cleaned_data = super().clean()
        password = cleaned_data.get("password")
        confirm_password = cleaned_data.get("confirm_password")

        if password and confirm_password and password != confirm_password:
            self.add_error("confirm_password", "⚠️ Passwords do not match.")


from django import forms
from .models import CustomUser
from members.models import ChurchMember

class ForgotPasswordForm(forms.ModelForm):
    """
    Form to reset the username and password for Church Members.
    """
    member_id = forms.CharField(
        max_length=20,
        required=True,
        label="Member ID",
        widget=forms.TextInput(attrs={
            'placeholder': '🆔 Enter your Church Member ID',
            'style': 'width: 100%; padding: 12px; border-radius: 25px;'
        }),
    )

    new_username = forms.CharField(
        max_length=150,
        required=True,
        widget=forms.TextInput(attrs={
            'placeholder': '👤 Enter your new username',
        }),
    )

    new_password = forms.CharField(
        widget=forms.PasswordInput(attrs={
            'placeholder': '🔒 Enter your new password',
        }),
        required=True,
    )

    confirm_password = forms.CharField(
        widget=forms.PasswordInput(attrs={
            'placeholder': '🔑 Confirm your new password',
        }),
        required=True,
    )

    class Meta:
        model = CustomUser
        fields = ['member_id', 'new_username', 'new_password', 'confirm_password']

    def clean_member_id(self):
        """
        Validate if the entered member ID exists in the ChurchMember model.
        """
        member_id = self.cleaned_data['member_id']
        try:
            member = ChurchMember.objects.get(member_id=member_id)
            return member
        except ChurchMember.DoesNotExist:
            raise forms.ValidationError("❌ The system does not recognize this ID. Please contact the admin at +255767972343.")

    def clean(self):
        """
        Custom validation for password confirmation.
        """
        cleaned_data = super().clean()
        new_password = cleaned_data.get("new_password")
        confirm_password = cleaned_data.get("confirm_password")

        if new_password and confirm_password and new_password != confirm_password:
            self.add_error("confirm_password", "⚠️ Passwords do not match.")
