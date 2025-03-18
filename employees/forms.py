from django import forms
from django.contrib.auth.forms import UserCreationForm
from .models import Employee, Skill, EmployeeSkill, Experience
from django.core.validators import MinValueValidator, MaxValueValidator

class EditSkillsForm(forms.ModelForm):
    skills = forms.ModelMultipleChoiceField(
        queryset=Skill.objects.all(),
        widget=forms.CheckboxSelectMultiple,
        required=False
    )

    class Meta:
        model = Employee
        fields = ['skills']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        print(f"DEBUG - EditSkillsForm.__init__ - instance: {self.instance}")
        
        for skill in self.fields['skills'].queryset:
            # Ustawienie domyślnej wartości na podstawie istniejącego poziomu zaawansowania
            proficiency_level = EmployeeSkill.objects.filter(employee=self.instance, skill=skill).first()
            print(f"DEBUG - EditSkillsForm.__init__ - skill: {skill.id}, proficiency_level: {proficiency_level}")
            
            self.fields[f'proficiency_level_{skill.id}'] = forms.ChoiceField(
                choices=[
                    ('', 'Wybierz poziom'),
                    ('1', 'Junior'),
                    ('2', 'Mid'),
                    ('3', 'Senior')
                ],
                required=False,
                initial=proficiency_level.proficiency_level if proficiency_level else ''
            )
            print(f"DEBUG - EditSkillsForm.__init__ - field: proficiency_level_{skill.id}, initial: {self.fields[f'proficiency_level_{skill.id}'].initial}")


class GroupedTableForm(forms.Form):
    """
    Formularz grupujący pytania w sekcje (grupy).
    Zarówno grupy (group_idx), jak i pytania (question_idx) numerujemy od 1.
    """

    def __init__(self, *args, **kwargs):
        self.grouped_questions = kwargs.pop('grouped_questions', [])
        super().__init__(*args, **kwargs)

        # Iteracja przez grupy, numerowanie od 1
        for group_idx, group in enumerate(self.grouped_questions, start=1):
            group_name = group.get('name')
            questions = group.get('questions', [])

            # Dodaj ukryte pole z nazwą grupy (opcjonalne)
            self.fields[f'group_{group_idx}_name'] = forms.CharField(
                initial=group_name,
                widget=forms.HiddenInput(),
                required=False
            )

            # Iteracja po pytaniach w danej grupie, pytania też startują od 1
            for question_idx, question_text in enumerate(questions, start=1):
                field_name = f'group_{group_idx}_question_{question_idx}'
                self.fields[field_name] = forms.IntegerField(
                    label=question_text,
                    initial=0,
                    min_value=0,
                    max_value=10,
                    widget=forms.NumberInput(attrs={
                        'class': 'form-control',
                        'placeholder': 'Wprowadź wartość od 0 do 10'
                    })
                )

    def clean(self):
        """
        Walidacja: sprawdza, czy suma punktów w każdej grupie = 10.
        """
        cleaned_data = super().clean()

        # Ponownie iterujemy grupy (od 1)
        for group_idx, group in enumerate(self.grouped_questions, start=1):
            questions = group.get('questions', [])

            # Pytania też mają indeks od 1 do len(questions)
            sum_of_group = sum(
                cleaned_data.get(f'group_{group_idx}_question_{q_idx}', 0)
                for q_idx in range(1, len(questions) + 1)
            )

            if sum_of_group != 10:
                raise forms.ValidationError(
                    f"Suma punktów w grupie '{group['name']}' musi wynosić dokładnie 10."
                )

        return cleaned_data

class ExperienceForm(forms.ModelForm):
    class Meta:
        model = Experience
        fields = ['title', 'description', 'date_started', 'date_ended', 'image', 'project_file']
        widgets = {
            'date_started': forms.DateInput(attrs={'type': 'date'}),
            'date_ended': forms.DateInput(attrs={'type': 'date', 'required': False}),
            'description': forms.Textarea(attrs={'rows': 5}),
        }
        
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field_name, field in self.fields.items():
            field.widget.attrs['class'] = 'form-control'
        
        # Pole data zakończenia nie jest wymagane
        self.fields['date_ended'].required = False
