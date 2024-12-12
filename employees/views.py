from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from .forms import EmployeeRegistrationForm
from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from .forms import EditSkillsForm

def index(request):
    return render(request, 'employees/index.html')
def register_employee(request):
    if request.method == 'POST':
        form = EmployeeRegistrationForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('login')
    else:
        form = EmployeeRegistrationForm()
    return render(request, 'employees/register.html', {'form': form})





@login_required
def employee_profile(request):
    if not request.user.is_employee:  # Sprawdzamy pole is_employee
        return render(request, 'employees/profile.html', {
            'error': 'Nie jesteś pracownikiem!'
        })

    employee = request.user.profile  # Pobierz profil pracownika

    # Inicjalizacja formularza z obecnymi umiejętnościami
    form = EditSkillsForm(instance=employee)

    if request.method == 'POST':
        form = EditSkillsForm(request.POST, instance=employee)
        if form.is_valid():
            form.save()  # Zapisz zmienione umiejętności
            return redirect('profile')  # Odśwież profil po zapisaniu

    return render(request, 'employees/profile.html', {
        'first_name': request.user.first_name,
        'last_name': request.user.last_name,
        'email': request.user.email,
        'form': form,  # Przekaż formularz do szablonu
    })


