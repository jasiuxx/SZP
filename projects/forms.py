from django import forms
from employees.models import Skill
from .models import Project, ProjectSkillRequirement

class ProjectForm(forms.ModelForm):
    class Meta:
        model = Project
        fields = ['title', 'code', 'description']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Dynamicznie dodaj pola dla każdej umiejętności
        for skill in Skill.objects.all():
            self.fields[f'skill_{skill.id}'] = forms.IntegerField(
                label=f"{skill.name}",
                min_value=0,
                required=False,
                initial=0,
                widget=forms.NumberInput(attrs={'class': 'form-control'})
            )



class ProjectSkillRequirementForm(forms.Form):
    skill = forms.ModelChoiceField(
        queryset=Skill.objects.all(),
        widget=forms.HiddenInput(),  # Ukryte pole
        required=False
    )
    required_count = forms.IntegerField(
        min_value=0,
        initial=0,
        widget=forms.NumberInput(attrs={'class': 'form-control', 'placeholder': 'Liczba specjalistów'}),
        required=False
    )

    def __init__(self, *args, **kwargs):
        skill = kwargs.pop('skill', None)
        super().__init__(*args, **kwargs)
        if skill:
            self.fields['skill'].initial = skill