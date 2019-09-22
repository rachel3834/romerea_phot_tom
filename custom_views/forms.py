from tom_targets.models import Target, TargetExtra
from django import forms

class TargetNameForm(forms.ModelForm):
    class Meta:
        model = Target
        fields = ('name',)


class TargetPositionForm(forms.ModelForm):
    class Meta:
        model = Target
        fields = ('ra','dec')
    radius = forms.FloatField(label='radius', min_value=0.001, max_value=1.0)
