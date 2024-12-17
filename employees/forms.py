from django import forms
from django.contrib.auth.forms import UserCreationForm
from .models import Employee, Skill



class EditSkillsForm(forms.ModelForm):
    skills = forms.ModelMultipleChoiceField(
        queryset=Skill.objects.all(),
        widget=forms.CheckboxSelectMultiple,  # lub SelectMultiple
        required=False  # Pole opcjonalne (możliwość odznaczenia wszystkich)
    )

    class Meta:
        model = Employee
        fields = ['skills']  # Pole, które chcemy edytować
