from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from .forms import EmployeeRegistrationForm


def register_employee(request):
    if request.method == 'POST':
        form = EmployeeRegistrationForm(request.POST)
        if form.is_valid():
            form.save()
            pass  # Redirect to login after registration
    else:
        form = EmployeeRegistrationForm()
    return render(request, 'employees/register.html', {'form': form})


@login_required
def employee_profile(request):
    if request.user.is_employee:  # Sprawdzamy pole is_employee
        return render(request, 'employees/profile.html', {
            'first_name': request.user.first_name,
            'last_name': request.user.last_name,
            'email': request.user.email,
        })
    else:
        return render(request, 'employees/profile.html', {
            'error': 'Nie jesteś pracownikiem!'
        })
