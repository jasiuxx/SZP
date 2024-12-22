from django import forms
from django.contrib.auth.forms import UserCreationForm
from .models import Employee, Skill
from django.core.validators import MinValueValidator, MaxValueValidator




from django import forms

from django import forms

class GroupedTableForm(forms.Form):
    def __init__(self, *args, grouped_questions=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.grouped_questions = grouped_questions or []

        for group_index, group in enumerate(self.grouped_questions, start=1):
            for question_index, question in enumerate(group['questions'], start=1):
                field_name = f"group_{group_index}_question_{question_index}"
                self.fields[field_name] = forms.IntegerField(
                    label=question,
                    widget=forms.NumberInput(attrs={
                        'class': 'form-control',
                        'min': 0,
                        'max': 10,
                        'placeholder': 'Wpisz liczbę od 0 do 10'
                    }),
                    min_value=0,
                    max_value=10,
                    required=True
                )




    def clean(self):
        cleaned_data = super().clean()

        # Sprawdzenie sumy punktów w każdej sekcji
        section_totals = {group_index: 0 for group_index in range(1, len(self.grouped_questions) + 1)}
        for field_name, value in cleaned_data.items():
            if value is not None:
                # Wyodrębnij numer sekcji z nazwy pola
                section_id = int(field_name.split('_')[1])
                section_totals[section_id] += value

        # Walidacja: suma punktów w każdej sekcji nie może przekroczyć 10
        for section_id, total in section_totals.items():
            if total > 10:
                raise forms.ValidationError(
                    f"Suma punktów w sekcji {section_id} nie może być większa niż 10. Obecna suma: {total}."
                )

        return cleaned_data
class EditSkillsForm(forms.ModelForm):
    skills = forms.ModelMultipleChoiceField(
        queryset=Skill.objects.all(),
        widget=forms.CheckboxSelectMultiple,  # lub SelectMultiple
        required=False  # Pole opcjonalne (możliwość odznaczenia wszystkich)
    )

    class Meta:
        model = Employee
        fields = ['skills']  # Pole, które chcemy edytować


class GroupedTableForm(forms.Form):
    def __init__(self, *args, **kwargs):
        self.grouped_questions = kwargs.pop('grouped_questions', [])
        super(GroupedTableForm, self).__init__(*args, **kwargs)
        for idx, group in enumerate(self.grouped_questions):
            group_name = group.get('name')
            questions = group.get('questions')
            self.fields[f'group_{idx+1}'] = forms.CharField(label=group_name, widget=forms.HiddenInput(), required=False)
            for q_idx, question in enumerate(questions):
                self.fields[f'group_{idx+1}_question_{q_idx+1}'] = forms.IntegerField(label=question, initial=0)

    def clean(self):
        cleaned_data = super().clean()
        for group_idx, group in enumerate(self.grouped_questions):
            sum_of_group = sum(cleaned_data[f'group_{group_idx + 1}_question_{q_idx + 1}'] for q_idx in range(len(group['questions'])))
            if sum_of_group != 10:
                self.add_error(f'group_{group_idx + 1}', f"The sum of the fields in '{group['name']}' must equal 10.")
