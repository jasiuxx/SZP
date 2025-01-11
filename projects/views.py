from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.db import transaction
from django.http import Http404
from django.views import View
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages

from employers.models import Employer
from .forms import ProjectForm
from .models import Project, Skill, ProjectSkillRequirement, EmployeeProjectAssignment
from employees.models import Employee

class ProjectCreateView(LoginRequiredMixin, View):
    login_url = '/login/'
    redirect_field_name = 'next'

    def get(pythf, request):
        if not request.user.is_employer:
            return redirect('profile')

        form = ProjectForm()
        skills = Skill.objects.all()
        return render(request, 'projects/create_project.html', {
            'form': form,
            'skills': skills,
            'suggested_employees': [],
        })

    def post(self, request):
        if not request.user.is_employer:
            return redirect('profile')

        form = ProjectForm(request.POST)
        skills = Skill.objects.all()

        # Obsługa sugerowania pracowników
        if 'suggest_employees' in request.POST:
            skill_requirements = {
                skill: int(request.POST.get(f'required_count_{skill.id}', 0))
                for skill in skills
                if int(request.POST.get(f'required_count_{skill.id}', 0)) > 0
            }

            suggested_employees = []
            for skill, required_count in skill_requirements.items():
                employees = Employee.objects.filter(skills=skill)[:required_count]
                suggested_employees.extend([
                    {
                        'first_name': employee.user.first_name,
                        'last_name': employee.user.last_name,
                        'email': employee.user.email,
                        'skill': skill.name,
                        'employee_id': employee.id
                    } for employee in employees
                ])

            return render(request, 'projects/create_project.html', {
                'form': form,
                'skills': skills,
                'suggested_employees': suggested_employees,
            })

        # Standardowa logika zapisu projektu
        if form.is_valid():
            project = form.save(commit=False)
            project.owner = request.user.employer
            project.save()

            # Zapis wymaganych umiejętności
            for skill in skills:
                required_count = int(request.POST.get(f'required_count_{skill.id}', 0))
                if required_count > 0:
                    ProjectSkillRequirement.objects.create(
                        project=project,
                        skill=skill,
                        required_count=required_count
                    )

            # Przypisanie pracowników
            for skill in skills:
                employees_to_assign = request.POST.getlist(f'assign_employee_{skill.id}')
                for employee_id in employees_to_assign:
                    employee = Employee.objects.get(id=employee_id)
                    project.employees.add(employee)
                    EmployeeProjectAssignment.objects.create(
                        project=project,
                        employee=employee,
                        skill=skill
                    )

            messages.success(request, "Projekt został utworzony.")
            return redirect('project_list')

        # Jeśli formularz jest niepoprawny
        return render(request, 'projects/create_project.html', {
            'form': form,
            'skills': skills,
            'suggested_employees': [],
        })


    def save_project(self, request, form, skills):
        if form.is_valid():
            project = form.save(commit=False)
            project.owner = request.user.employer
            project.save()

            # Zapis wymaganych umiejętności
            for skill in skills:
                required_count = int(request.POST.get(f'required_count_{skill.id}', 0))
                if required_count > 0:
                    ProjectSkillRequirement.objects.create(
                        project=project,
                        skill=skill,
                        required_count=required_count
                    )

            # Przypisanie pracowników do projektu
            self.assign_employees(request, project, skills)

            return redirect('project_list')
        else:
            # Jeśli formularz nie jest poprawny, zwróć formularz z błędami
            return render(request, 'projects/create_project.html', {
                'form': form,
                'skills': skills,
                'suggested_employees': [],
            })

    def suggest_employees(self, request, form, skills):
        skill_requirements = {
            skill: int(request.POST.get(f'required_count_{skill.id}', 0))
            for skill in skills
            if int(request.POST.get(f'required_count_{skill.id}', 0)) > 0
        }

        suggested_employees = []
        for skill, required_count in skill_requirements.items():
            employees = Employee.objects.filter(skills=skill)[:required_count]
            for employee in employees:
                suggested_employees.append({
                    'first_name': employee.user.first_name,
                    'last_name': employee.user.last_name,
                    'email': employee.user.email,
                    'skill': skill.name,
                    'employee_id': employee.id  # Przechowuj ID pracownika
                })

        return render(request, 'projects/create_project.html', {
            'form': form,
            'skills': skills,
            'suggested_employees': suggested_employees,
        })

    def assign_employees(self, request, project, skills):
        for skill in skills:
            required_count = int(request.POST.get(f'required_count_{skill.id}', 0))
            if required_count > 0:
                employees_to_assign = request.POST.getlist(f'assign_employee_{skill.id}')
                for employee_id in employees_to_assign:
                    employee = Employee.objects.get(id=employee_id)
                    # Przypisz pracownika do projektu
                    project.employees.add(employee)
                    # Przypisz umiejętność do pracownika w projekcie
                    EmployeeProjectAssignment.objects.create(project=project, employee=employee, skill=skill)
        return redirect('project_list')






@login_required
def project_list(request):
    try:
        employer = request.user.employer  # Pobranie obiektu Employer dla zalogowanego użytkownika
    except Employer.DoesNotExist:
        return redirect('error_page')  # Przekierowanie w przypadku braku uprawnień

    # Pobranie projektów z powiązaniami do pracowników i przypisanych umiejętności
    projects = employer.projects.prefetch_related(
        'employees',  # Powiązanie z pracownikami
        'employeeprojectassignment_set__skill'  # Powiązanie z przypisaniami i umiejętnościami
    )

    return render(request, 'projects/project_list.html', {'projects': projects})


class ProjectDeleteView(LoginRequiredMixin, View):
    login_url = '/login/'
    redirect_field_name = 'next'

    def post(self, request, project_id):
        # Znajdź projekt należący do zalogowanego pracodawcy
        project = get_object_or_404(
            Project,
            id=project_id,
            owner=request.user.employer
        )

        try:
            # Usuń projekt
            project.delete()
            messages.success(request, f"Projekt '{project.title}' został usunięty.")
        except Exception as e:
            # Obsługa błędów podczas usuwania
            messages.error(request, f"Nie można usunąć projektu: {str(e)}")

        return redirect('project_list')


@login_required
def edit_project(request, project_id):
    project = get_object_or_404(Project, id=project_id, owner=request.user.employer)
    skills = Skill.objects.all()

    # Funkcja pomocnicza do pobrania wymaganych umiejętności i przypisanych pracowników
    def get_project_data():
        skill_requirements = {
            req.skill.id: req.required_count for req in project.skill_requirements.all()
        }
        assigned_employees = {
            skill.id: list(project.employees.filter(skills=skill))
            for skill in skills
        }
        return skill_requirements, assigned_employees

    # Pobranie danych projektu
    skill_requirements, assigned_employees = get_project_data()

    if request.method == 'POST':
        form = ProjectForm(request.POST, instance=project, current_project=project)

        # Obsługa sugerowania pracowników
        if 'suggest_employees' in request.POST:
            suggested_employees = []
            for skill in skills:
                required_count = int(request.POST.get(f'required_count_{skill.id}', 0))
                if required_count > 0:
                    employees = Employee.objects.filter(skills=skill)[:required_count]
                    suggested_employees.extend([
                        {
                            'first_name': employee.user.first_name,
                            'last_name': employee.user.last_name,
                            'email': employee.user.email,
                            'skill': skill.name,
                            'employee_id': employee.id
                        } for employee in employees
                    ])

            return render(request, 'projects/edit_project.html', {
                'form': form,
                'skills': skills,
                'project': project,
                'suggested_employees': suggested_employees,
                'skill_requirements': skill_requirements,
                'assigned_employees': assigned_employees,
            })

        # Obsługa zapisu zmian w projekcie
        if form.is_valid():
            with transaction.atomic():
                project = form.save()

                # Aktualizacja wymagań dotyczących umiejętności
                ProjectSkillRequirement.objects.filter(project=project).delete()
                for skill in skills:
                    required_count = int(request.POST.get(f'required_count_{skill.id}', 0))
                    if required_count > 0:
                        ProjectSkillRequirement.objects.create(
                            project=project,
                            skill=skill,
                            required_count=required_count
                        )

                # Aktualizacja przypisanych pracowników
                project.employees.clear()
                EmployeeProjectAssignment.objects.filter(project=project).delete()
                for skill in skills:
                    employees_to_assign = request.POST.getlist(f'assign_employee_{skill.id}')
                    for employee_id in employees_to_assign:
                        employee = Employee.objects.get(id=employee_id)
                        project.employees.add(employee)
                        EmployeeProjectAssignment.objects.create(
                            project=project,
                            employee=employee,
                            skill=skill
                        )

                messages.success(request, "Projekt został zaktualizowany.")
                return redirect('project_list')

        # Obsługa błędów formularza
        messages.error(request, "Wystąpiły błędy w formularzu. Proszę poprawić i spróbować ponownie.")
        return render(request, 'projects/edit_project.html', {
            'form': form,
            'skills': skills,
            'project': project,
            'skill_requirements': skill_requirements,
            'assigned_employees': assigned_employees,
            'errors': form.errors,
        })

    # Obsługa żądania GET
    form = ProjectForm(instance=project, current_project=project)
    return render(request, 'projects/edit_project.html', {
        'form': form,
        'skills': skills,
        'project': project,
        'skill_requirements': skill_requirements,
        'assigned_employees': assigned_employees,
    })
