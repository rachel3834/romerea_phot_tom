from tom_targets.models import Target, TargetExtra
from django import forms

class TargetNameForm(forms.ModelForm):
    class Meta:
        model = Target
        fields = ('name',)
