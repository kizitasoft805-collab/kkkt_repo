# languages/forms.py

from django import forms

LANGUAGE_CHOICES = [
    ('en', 'English'),
    ('sw', 'Kiswahili'),
]

class LanguageSelectForm(forms.Form):
    preferred_language = forms.ChoiceField(
        choices=LANGUAGE_CHOICES,
        widget=forms.RadioSelect,  # or forms.Select
        label="Select your language"
    )
