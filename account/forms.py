from django import forms
from django.contrib.auth.forms import UserCreationForm
from .models import CustomUser
from employees.models import Employee

class EmployeeRegistrationForm(UserCreationForm):
    first_name = forms.CharField(max_length=30, required=True)
    last_name = forms.CharField(max_length=30, required=True)

    class Meta:
        model = CustomUser
        fields = ['username', 'first_name', 'last_name', 'email', 'password1', 'password2']

    def save(self, commit=True):
        user = super().save(commit=False)
        user.is_employee = True  # Automatyczne oznaczenie użytkownika jako pracownika
        if commit:
            user.save()
            # Tworzenie powiązanego profilu Employee w aplikacji employees
            Employee.objects.create(user=user)
        return user
