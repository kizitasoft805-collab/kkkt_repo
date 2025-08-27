# evangelist/forms.py
from django import forms
from django.forms import inlineformset_factory
from .models import EvangelistReport, ElderDuty
from leaders.models import Leader


class EvangelistReportForm(forms.ModelForm):
    """Main report form."""

    class Meta:
        model  = EvangelistReport
        fields = [
            "date_given",
            "children_count",
            "adults_count",
            "count_10000",
            "count_5000",
            "count_2000",
            "count_1000",
            "count_500",
            "count_200",
            "count_100",
            "count_50",
        ]
        widgets = {
            "date_given": forms.DateInput(attrs={"type": "date"}),
        }


class ElderDutyForm(forms.ModelForm):
    """Single elder‑on‑duty row (dropdown limited to Elders)."""

    elder = forms.ModelChoiceField(
        queryset=Leader.objects.filter(occupation="Elder"),
        label="Elder on duty"
    )

    class Meta:
        model  = ElderDuty
        fields = ["elder"]


ElderDutyFormSet = inlineformset_factory(
    parent_model=EvangelistReport,
    model=ElderDuty,
    form=ElderDutyForm,
    extra=1,
    can_delete=False,
)
