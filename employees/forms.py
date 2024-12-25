from django import forms
from django.contrib.auth.forms import UserCreationForm
from .models import Employee, Skill
from django.core.validators import MinValueValidator, MaxValueValidator
from django import forms
from django import forms
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

        # Iteracja przez grupy i pytania
        for group_idx, group in enumerate(self.grouped_questions):
            group_name = group.get('name')
            questions = group.get('questions', [])

            # Dodaj ukryte pole dla nazwy grupy (opcjonalne)
            self.fields[f'group_{group_idx}_name'] = forms.CharField(
                initial=group_name,
                widget=forms.HiddenInput(),
                required=False
            )

            # Dodaj pola dla każdego pytania w grupie
            for question_idx, question_text in enumerate(questions):
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
        cleaned_data = super().clean()

        # Sprawdź sumę punktów dla każdej grupy
        for group_idx, group in enumerate(self.grouped_questions):
            questions = group.get('questions', [])
            sum_of_group = sum(
                cleaned_data.get(f'group_{group_idx}_question_{q_idx}', 0)
                for q_idx in range(len(questions))
            )

            # Jeśli suma punktów w grupie nie wynosi 10, zgłoś błąd
            if sum_of_group != 10:
                raise forms.ValidationError(
                    f"Suma punktów w grupie '{group['name']}' musi wynosić dokładnie 10."
                )

        return cleaned_data