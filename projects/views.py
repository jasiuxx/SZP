from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required

from employers.models import Employer
from .forms import ProjectForm, ProjectSkillRequirementForm
from .models import Project, ProjectSkillRequirement, Skill

@login_required
def create_project(request):
    if not request.user.is_employer:
        return redirect('profile')

    if request.method == 'POST':
        form = ProjectForm(request.POST)
        if form.is_valid():
            project = form.save(commit=False)
            project.owner = request.user.employer
            project.save()

            # Przetwarzanie umiejętności
            for skill in Skill.objects.all():
                required_count = request.POST.get(f'required_count_{skill.id}', 0)
                if int(required_count) > 0:
                    ProjectSkillRequirement.objects.create(
                        project=project,
                        skill=skill,
                        required_count=int(required_count)
                    )

            return redirect('project_list')
    else:
        form = ProjectForm()

    # Przygotuj listę umiejętności z formularzami
    skills = Skill.objects.all()
    skill_forms = [
        ProjectSkillRequirementForm(skill=skill, prefix=f'skill_{skill.id}')
        for skill in skills
    ]

    return render(request, 'projects/create_project.html', {
        'form': form,
        'skills': skills,
        'skill_forms': skill_forms,
    })





@login_required
def project_list(request):
    try:
        employer = request.user.employer  # Pobranie obiektu Employer dla zalogowanego użytkownika
    except Employer.DoesNotExist:
        return redirect('error_page')  # Przekierowanie w przypadku braku uprawnień

    projects = employer.projects.all()  # Projekty utworzone przez danego pracodawcę
    return render(request, 'projects/project_list.html', {'projects': projects})

