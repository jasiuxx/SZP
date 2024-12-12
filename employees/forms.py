from django import forms
from django.contrib.auth.forms import UserCreationForm
from .models import CustomUser, Employee, Skill

class EmployeeRegistrationForm(UserCreationForm):
    first_name = forms.CharField(max_length=30)
    last_name = forms.CharField(max_length=30)
    skills = forms.ModelMultipleChoiceField(
        queryset=Skill.objects.all(),
        widget=forms.CheckboxSelectMultiple,  # lub SelectMultiple
        required=False
    )

    class Meta:
        model = CustomUser
        fields = ['username', 'first_name', 'last_name', 'email', 'password1', 'password2']  # Usuń skills

    def save(self, commit=True):
        user = super().save(commit=False)
        user.is_employee = True
        if commit:
            user.save()
            employee = Employee.objects.create(user=user)
            # Ustawienie umiejętności dla pracownika
            employee.skills.set(self.cleaned_data['skills'])
        return user

class EditSkillsForm(forms.ModelForm):
    skills = forms.ModelMultipleChoiceField(
        queryset=Skill.objects.all(),
        widget=forms.CheckboxSelectMultiple,  # lub SelectMultiple
        required=False  # Pole opcjonalne (możliwość odznaczenia wszystkich)
    )

    class Meta:
        model = Employee
        fields = ['skills']  # Pole, które chcemy edytować
