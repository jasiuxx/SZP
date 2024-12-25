from django import forms
from .models import Project
from employees.models import Skill

class ProjectForm(forms.ModelForm):
    skills_required = forms.ModelMultipleChoiceField(
        queryset=Skill.objects.all(),
        widget=forms.CheckboxSelectMultiple,
        required=True
    )

    class Meta:
        model = Project
        fields = ['title', 'code', 'description', 'skills_required']
