from django.shortcuts import render, redirect
from django.contrib.auth import login
from .forms import UserRegistrationForm
from employees.forms import EditSkillsForm
from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from employees.models import Employee

def register(request):
    if request.method == 'POST':
        form = UserRegistrationForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('login')  # Przekierowanie po rejestracji
    else:
        form = UserRegistrationForm()

    return render(request, 'account/register.html', {'form': form})


def index(request):
    return render(request, 'account/index.html')



@login_required
def profile_view(request):
    """
    Wyświetla profil użytkownika. Pracownik może edytować swoje umiejętności,
    a pracodawca ma dostęp do zarządzania projektami.
    """
    if request.user.is_employee:
        try:
            employee = request.user.profile  # Pobierz profil pracownika
            form = EditSkillsForm(instance=employee)

            if request.method == 'POST':
                form = EditSkillsForm(request.POST, instance=employee)
                if form.is_valid():
                    form.save()
                    return redirect('profile')  # Odśwież stronę profilu
            return render(request, 'account/profile.html', {
                'first_name': request.user.first_name,
                'last_name': request.user.last_name,
                'email': request.user.email,
                'form': form
            })
        except Employee.DoesNotExist:
            # Przekierowanie do profilu pracodawcy, jeśli brak profilu pracownika
            return redirect('employer_profile')
    elif request.user.is_employer:
        # Pracodawca - wyświetl profil pracodawcy
        return render(request, 'account/employer_profile.html')
    else:
        return render(request, 'account/profile.html', {
            'error': 'Nie masz przypisanego profilu.'
        })



@login_required
def employer_profile(request):
    """
    Wyświetla profil pracodawcy.
    """
    if not request.user.is_employer:
        return redirect('profile')  # Przekierowanie dla użytkowników bez uprawnień

    return render(request, 'account/employer_profile.html')
