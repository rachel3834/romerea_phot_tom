from tom_targets.models import Target, TargetExtra
from django import forms

class TargetNameForm(forms.ModelForm):
    class Meta:
        model = Target
        fields = ('name',)


class TargetPositionForm(forms.Form):
    class Meta:
        fields = ('ra','dec','radius',)

    ra = forms.FloatField(label='ra', min_value=0.0, max_value=360.0)
    dec = forms.FloatField(label='dec', min_value=-90.0, max_value=90.0)
    radius = forms.FloatField(label='radius', min_value=0.001, max_value=3600.0)
