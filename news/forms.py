from django import forms
from .models import News, NewsMedia

class NewsForm(forms.ModelForm):
    """
    Form for creating a news post with well-styled fields.
    Includes asterisks (*) for required fields.
    """
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Adding an asterisk (*) to required fields
        self.fields['title'].label = "📰 News Title *"
        self.fields['content'].label = "✍️ News Content *"

    class Meta:
        model = News
        fields = ['title', 'content', 'bible_reference']
        widgets = {
            'title': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': '📰 Enter News Title',
                'style': 'border-radius: 25px; padding: 10px; width: 90%; font-size: 16px;'
            }),
            'content': forms.Textarea(attrs={
                'class': 'form-control',
                'placeholder': '✍️ Enter News Content',
                'style': 'border-radius: 25px; padding: 10px; width: 90%; height: 150px; font-size: 16px;'
            }),
            'bible_reference': forms.Textarea(attrs={
                'class': 'form-control',
                'placeholder': '📖 Enter Bible Reference (Optional) (e.g. John 3:16, Romans 8:28)',
                'style': 'border-radius: 25px; padding: 10px; width: 90%; height: 100px; font-size: 16px;'
            }),
        }

class NewsMediaForm(forms.ModelForm):
    """
    Form for uploading multiple media files dynamically.
    """
    class Meta:
        model = NewsMedia
        fields = ['media_type', 'file']
        widgets = {
            'media_type': forms.Select(attrs={
                'class': 'form-control media-type',
                'style': 'border-radius: 25px; padding: 10px; width: 100%; font-size: 16px;',
            }),
            'file': forms.ClearableFileInput(attrs={
                'class': 'form-control media-file',
                'style': 'border-radius: 25px; padding: 10px; width: 100%; font-size: 16px;',
            }),
        }
