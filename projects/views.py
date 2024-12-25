from django.http import HttpResponseForbidden
from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from .forms import ProjectForm

@login_required
def create_project(request):
    # Sprawdź, czy użytkownik jest pracodawcą
    if not request.user.is_employer:
        return HttpResponseForbidden("Nie masz uprawnień do wykonania tej akcji.")  # Odpowiedź HTTP 403

    try:
        employer = request.user.employer  # Pobranie obiektu Employer dla zalogowanego użytkownika
    except AttributeError:
        return HttpResponseForbidden("Nie masz przypisanego profilu pracodawcy.")  # Odpowiedź HTTP 403

    if request.method == 'POST':
        form = ProjectForm(request.POST)
        if form.is_valid():
            project = form.save(commit=False)
            project.owner = employer  # Ustawienie właściciela projektu
            project.save()
            form.save_m2m()  # Zapisanie relacji wiele-do-wielu (skills_required)
            return redirect('project_list')  # Przekierowanie na listę projektów
    else:
        form = ProjectForm()
    return render(request, 'projects/create_project.html', {'form': form})



@login_required
def project_list(request):
    try:
        employer = request.user.employer  # Pobranie obiektu Employer dla zalogowanego użytkownika
    except Employer.DoesNotExist:
        return redirect('error_page')  # Przekierowanie w przypadku braku uprawnień

    projects = employer.projects.all()  # Projekty utworzone przez danego pracodawcę
    return render(request, 'projects/project_list.html', {'projects': projects})

