from django import forms
from employees.models import Skill
from .models import Project, ProjectSkillRequirement
from django.core.exceptions import ValidationError
from django.utils.translation import gettext_lazy as _


class ProjectForm(forms.ModelForm):
    class Meta:
        model = Project
        fields = ['title', 'code', 'description']
        error_messages = {
            'title': {
                'unique': _('Projekt o takim tytule już istnieje.')
            },
            'code': {
                'unique': _('Projekt o takim kodzie już istnieje.')
            },
        }

    def __init__(self, *args, **kwargs):
        # Wyciągnij current_project, jeśli jest przekazany
        current_project = kwargs.pop('current_project', None)

        # Wywołaj oryginalny konstruktor
        super().__init__(*args, **kwargs)

        # Dodaj atrybut instancji, jeśli current_project został przekazany
        self.current_project = current_project

        # Reszta oryginalnej logiki
        for skill in Skill.objects.all():
            self.fields[f'skill_{skill.id}'] = forms.IntegerField(
                label=f"{skill.name}",
                min_value=0,
                required=False,
                initial=0,
                widget=forms.NumberInput(attrs={'class': 'form-control'})
            )

    def clean_title(self):
        title = self.cleaned_data.get('title')

        # Sprawdź, czy tytuł jest już zajęty, z wyłączeniem bieżącego projektu
        existing_projects = Project.objects.filter(title=title)

        if self.current_project:
            existing_projects = existing_projects.exclude(pk=self.current_project.pk)

        if existing_projects.exists():
            raise ValidationError('Projekt o takim tytule już istnieje.')

        return title

    def clean_code(self):
        code = self.cleaned_data.get('code')

        # Sprawdź, czy kod jest już zajęty, z wyłączeniem bieżącego projektu
        existing_projects = Project.objects.filter(code=code)

        if self.current_project:
            existing_projects = existing_projects.exclude(pk=self.current_project.pk)

        if existing_projects.exists():
            raise ValidationError('Projekt o takim kodzie już istnieje.')

        return code



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