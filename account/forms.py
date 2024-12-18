from django import forms
from django.contrib.auth.forms import UserCreationForm
from account.models import CustomUser
from employers.models import Employer
from employees.models import Employee
from employers.models import VerificationCode

class UserRegistrationForm(UserCreationForm):
    is_employer = forms.BooleanField(
        required=False,
        label="Rejestruj się jako pracodawca",
        widget=forms.CheckboxInput(attrs={"class": "form-check-input"})
    )
    verification_code = forms.CharField(
        max_length=50,
        required=False,
        label="Kod weryfikacyjny",
        widget=forms.TextInput(attrs={"class": "form-control", "placeholder": "Podaj kod weryfikacyjny"})
    )

    class Meta:
        model = CustomUser
        fields = ["username", "first_name", "last_name", "email", "password1", "password2"]

    def clean(self):
        cleaned_data = super().clean()
        is_employer = cleaned_data.get("is_employer")
        verification_code = cleaned_data.get("verification_code")

        if is_employer:
            if not verification_code:
                raise forms.ValidationError("Pracodawcy muszą podać kod weryfikacyjny.")
            try:
                code_instance = VerificationCode.objects.get(code=verification_code, is_used=False)
            except VerificationCode.DoesNotExist:
                raise forms.ValidationError("Podany kod weryfikacyjny jest nieprawidłowy lub już został wykorzystany.")

            self.verification_code_instance = code_instance

        return cleaned_data

    def save(self, commit=True):
        user = super().save(commit=False)
        is_employer = self.cleaned_data.get("is_employer")

        if is_employer:
            user.is_employer = True
            user.save()
            employer = Employer.objects.create(user=user)
            self.verification_code_instance.is_used = True
            self.verification_code_instance.employer = employer  # Przypisz kod do pracodawcy
            self.verification_code_instance.save()
        else:
            user.is_employee = True
            user.save()
            Employee.objects.create(user=user)

        return user
