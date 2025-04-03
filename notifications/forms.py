from django import forms
from .models import Notification
from members.models import ChurchMember

class NotificationForm(forms.ModelForm):
    """
    Form to create and send notifications to Church Members.
    (Leaders are included under members)
    """

    class Meta:
        model = Notification
        fields = ['title', 'message']
        widgets = {
            'title': forms.TextInput(attrs={
                'placeholder': '📢 Enter Notification Title',
                'style': 'width: 100vw; max-width: 100%; min-width: 100%; padding: 15px; '
                         'border-radius: 25px; border: 1px solid #ccc; font-size: 18px; '
                         'background: #f9f9f9; outline: none; transition: 0.3s; display: block; '
                         'text-align: left; box-sizing: border-box;'
            }),
            'message': forms.Textarea(attrs={
                'rows': 4,
                'placeholder': '✉️ Type your message here...',
                'style': 'width: 100vw; max-width: 100%; min-width: 100%; padding: 15px; '
                         'border-radius: 25px; border: 1px solid #ccc; font-size: 18px; '
                         'background: #f9f9f9; outline: none; transition: 0.3s; display: block; '
                         'resize: none; height: 120px; text-align: left; box-sizing: border-box;'
            }),
        }
