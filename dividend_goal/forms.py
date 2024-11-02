from django import forms
from .models import DividendGoal

class DividendGoalForm(forms.ModelForm):
    class Meta:
        model = DividendGoal
        fields = ['annual_goal']