from django import forms
from .models import Brand


class BrandForm(forms.Form):
    """
    Форма для выбора марки авто.
    """

    brand = forms.ModelChoiceField(
        queryset=Brand.objects.all(),
        empty_label=None,
        widget=forms.Select(attrs={'class': 'form-select'})
    )
