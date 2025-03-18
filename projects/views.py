from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.db import transaction
from django.http import Http404
from django.views import View
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages

from employers.models import Employer
from .forms import ProjectForm, ProjectMessageForm
from .models import Project, Skill, ProjectSkillRequirement, EmployeeProjectAssignment, ProjectMessage
from employees.models import Employee, EmployeeSkill

import random
import math
from copy import deepcopy

# Kategorie Belbina
BELBIN_CATEGORIES = {
    'socjalne': ['NG', 'CZG', 'CZK'],
    'intelektualne': ['SE', 'SIE'],
    'zadaniowe': ['PO', 'CZA', 'PER'],
}

def has_high_role_in_category(employee, category, level=None):
    """
    Sprawdza, czy pracownik ma rolę z danej kategorii na poziomie 'bardzo wysoki' lub 'wysoki'.
    """
    if not employee.belbin_test_result:
        return False
        
    roles = BELBIN_CATEGORIES[category]
    # Pobieramy role z odpowiedniego poziomu z JSONa
    roles_by_level = employee.belbin_test_result.get('roles_by_level', {})
    
    # Jeśli poziom nie jest podany, sprawdzamy wszystkie poziomy
    if level is None:
        return any(role in roles_by_level.get('bardzo wysoki', []) for role in roles) or \
               any(role in roles_by_level.get('wysoki', []) for role in roles)
    
    # Sprawdzamy tylko dla podanego poziomu
    employee_roles = roles_by_level.get(level, [])
    return any(role in employee_roles for role in roles)


def suggest_team_members(required_skills, project=None):
    """
    Funkcja sugeruje pracowników na podstawie wymagań (required_skills), przy czym
    dąży do utworzenia zespołu z różnorodnymi rolami Belbina, patrząc na cały zespół,
    a nie tylko na poszczególne umiejętności.
    
    :param required_skills: słownik, gdzie klucz to obiekt Skill, a wartość to liczba wymaganych pracowników
    :param project: opcjonalnie projekt (może być użyty do dodatkowego filtrowania)
    :return: lista słowników zawierających dane pracowników i nazwę skillu
    """
    suggested_employees = []
    already_selected = set()  # Zbiór identyfikatorów już wybranych pracowników
    team_roles = {
        'bardzo wysoki': {},
        'wysoki': {}
    }  # Słownik do śledzenia ról Belbina w całym zespole

    # Sortowanie wymagań (skill, count) malejąco według count
    sorted_skills = sorted(required_skills.items(), key=lambda x: x[1], reverse=True)

    for skill, required_count in sorted_skills:
        if required_count <= 0:
            continue

        # Pobieramy wszystkie kwalifikowane osoby posiadające dany skill
        qualified_employees = list(
            Employee.objects.filter(skills=skill).exclude(id__in=already_selected)
        )
        selected_for_skill = []
        remaining_count = required_count

        # Lista kategorii – kolejność iteracji (można ją dowolnie modyfikować)
        categories = list(BELBIN_CATEGORIES.keys())

        # Funkcja pomocnicza, która wybiera pracownika z danej kategorii określonego poziomu,
        # uwzględniając już wybrane role w całym zespole
        def pick_candidate(level):
            candidate_found = False
            nonlocal remaining_count  # Deklaracja nonlocal musi być na początku funkcji
            
            # Sortujemy kategorie według liczby już wybranych ról w całym zespole (rosnąco)
            # Dzięki temu preferujemy kategorie, które są najmniej reprezentowane w zespole
            sorted_categories = sorted(
                categories,
                key=lambda cat: sum(team_roles[level].get(role, 0) for role in BELBIN_CATEGORIES[cat])
            )
            
            for category in sorted_categories:
                # Pobieramy wszystkie role z danej kategorii
                category_roles = BELBIN_CATEGORIES[category]
                
                # Sortujemy role według liczby już wybranych pracowników z tą rolą (rosnąco)
                # Dzięki temu preferujemy role, które są najmniej reprezentowane w zespole
                sorted_roles = sorted(
                    category_roles,
                    key=lambda role: team_roles[level].get(role, 0)
                )
                
                # Dla każdej roli, próbujemy znaleźć pracownika
                for role in sorted_roles:
                    # Szukamy pracownika nie wybranego jeszcze, z daną rolą na danym poziomie
                    for employee in qualified_employees:
                        if employee.id in already_selected or employee in selected_for_skill:
                            continue
                        
                        # Sprawdzamy, czy pracownik ma daną rolę na danym poziomie
                        if employee.belbin_test_result:
                            roles_by_level = employee.belbin_test_result.get('roles_by_level', {})
                            employee_roles = roles_by_level.get(level, [])
                            
                            if role in employee_roles:
                                # Dodajemy role pracownika do śledzenia ról w zespole
                                for r in employee_roles:
                                    team_roles[level][r] = team_roles[level].get(r, 0) + 1
                                
                                selected_for_skill.append(employee)
                                already_selected.add(employee.id)
                                remaining_count -= 1
                                candidate_found = True
                                
                                # Jeśli osiągnięto wymaganą liczbę, kończymy rundę
                                if remaining_count <= 0:
                                    return True
                                
                                # Jeśli znalazło się kandydata dla tej roli, przechodzimy do kolejnej roli
                                break
                
                # Jeśli nie znaleziono kandydata dla żadnej roli, próbujemy znaleźć kandydata z jakąkolwiek rolą z tej kategorii
                if not candidate_found:
                    for employee in qualified_employees:
                        if employee.id in already_selected or employee in selected_for_skill:
                            continue
                        if has_high_role_in_category(employee, category, level):
                            # Dodajemy role pracownika do śledzenia ról w zespole
                            if employee.belbin_test_result:
                                roles_by_level = employee.belbin_test_result.get('roles_by_level', {})
                                for role in roles_by_level.get(level, []):
                                    team_roles[level][role] = team_roles[level].get(role, 0) + 1
                            
                            selected_for_skill.append(employee)
                            already_selected.add(employee.id)
                            remaining_count -= 1
                            candidate_found = True
                            
                            # Jeśli osiągnięto wymaganą liczbę, kończymy rundę
                            if remaining_count <= 0:
                                return True
                            
                            # Jeśli znalazło się kandydata dla tej kategorii, przechodzimy do kolejnej kategorii
                            break
            return candidate_found

        # Round-robin – najpierw próba wyboru kandydatów z poziomu 'bardzo wysoki'
        while remaining_count > 0:
            if not pick_candidate('bardzo wysoki'):
                break  # Jeśli w całej rundzie nie uda się znaleźć kandydata, wychodzimy z pętli

        # Jeżeli nadal brakuje kandydatów, powtórz round-robin dla poziomu 'wysoki'
        if remaining_count > 0:
            while remaining_count > 0:
                if not pick_candidate('wysoki'):
                    break

        # Jeśli nadal nie zapełniono zamówienia, uzupełniamy pozostałymi kwalifikowanymi pracownikami
        if remaining_count > 0:
            for employee in qualified_employees:
                if remaining_count <= 0:
                    break
                if employee.id in already_selected or employee in selected_for_skill:
                    continue
                selected_for_skill.append(employee)
                already_selected.add(employee.id)
                remaining_count -= 1

        # Formatowanie wyniku dla danego skillu – dodajemy dane pracowników do listy wynikowej
        for employee in selected_for_skill:
            suggested_employees.append({
                'first_name': employee.user.first_name,
                'last_name': employee.user.last_name,
                'email': employee.user.email,
                'skill': skill.name,
                'employee_id': employee.id
            })

    return suggested_employees


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
            'skill_requirements': {},
        })

    def post(self, request):
        if not request.user.is_employer:
            return redirect('profile')
        
        form = ProjectForm(request.POST)
        skills = Skill.objects.all()
        
        # Przygotowanie słownika z danymi o wymaganiach
        skill_requirements = {}
        skill_requirements_by_id = {}  # Słownik z ID umiejętności jako kluczami
        for skill in skills:
            required_count = int(request.POST.get(f'required_count_{skill.id}', 0))
            if required_count > 0: 
                skill_requirements[skill] = required_count
                skill_requirements_by_id[skill.id] = required_count

        # Jeśli kliknięto przycisk "Sugeruj pracowników", tylko generuj sugestie
        if 'suggest_employees' in request.POST:
            # Nie zapisujemy projektu – tworzymy tymczasowy obiekt tylko do obliczeń
            suggested_employees = suggest_team_members_with_annealing(None, skill_requirements)
            
            # Sprawdź, czy dla każdej umiejętności znaleziono wystarczającą liczbę pracowników
            skill_counts = {}
            for employee in suggested_employees:
                skill_name = employee['skill']
                skill_counts[skill_name] = skill_counts.get(skill_name, 0) + 1
            
            # Dodaj komunikaty o brakujących pracownikach
            for skill, required_count in skill_requirements.items():
                skill_name = skill.name
                found_count = skill_counts.get(skill_name, 0)
                if found_count < required_count:
                    messages.warning(
                        request, 
                        f"Nie znaleziono wystarczającej liczby pracowników z umiejętnością {skill_name}. "
                        f"Wymagano: {required_count}, znaleziono: {found_count}."
                    )
            
            # Renderuj stronę z formularzem, listą skills, sugestiami oraz danymi z formularza
            return render(request, 'projects/create_project.html', {
                'form': form,
                'skills': skills,
                'suggested_employees': suggested_employees,
                'skill_requirements': skill_requirements_by_id,  # Przekazanie wymagań z ID jako kluczami
            })

        # Jeśli kliknięto przycisk "Zapisz projekt", wykonaj zapis
        if form.is_valid():
            # Tworzymy obiekt projektu, ustawiamy właściciela i zapisujemy
            project = form.save(commit=False)
            project.owner = request.user.employer
            project.save()

            # Zapis wymaganych umiejętności
            for skill, required_count in skill_requirements.items():
                ProjectSkillRequirement.objects.create(
                    project=project,
                    skill=skill,
                    required_count=required_count
                )

            # Automatyczne przypisanie pracowników na podstawie sugerowanej listy
            suggested_employees = suggest_team_members_with_annealing(project.id, skill_requirements)
            for employee in suggested_employees:
                skill_instance = Skill.objects.get(name=employee['skill'])
                project.employees.add(Employee.objects.get(id=employee['employee_id']))
                EmployeeProjectAssignment.objects.create(
                    project=project,
                    employee=Employee.objects.get(id=employee['employee_id']),
                    skill=skill_instance
                )

            messages.success(request, "Projekt został utworzony i pracownicy zostali przypisani automatycznie.")
            return redirect('project_list')

        # W przypadku błędów walidacji (dla obu scenariuszy) renderuj formularz z komunikatami
        return render(request, 'projects/create_project.html', {
            'form': form,
            'skills': skills,
            'suggested_employees': [],
            'skill_requirements': skill_requirements_by_id,  # Przekazanie wymagań z ID jako kluczami
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

    # Pobierz aktualne wymagania dotyczące umiejętności
    skill_requirements = {req.skill.id: req.required_count for req in project.skill_requirements.all()}

    # Pobierz przypisanych pracowników
    assigned_employees = {
        skill.id: [
            {
                'id': assignment.employee.id,
                'first_name': assignment.employee.user.first_name,
                'last_name': assignment.employee.user.last_name,
                'email': assignment.employee.user.email,
            }
            for assignment in EmployeeProjectAssignment.objects.filter(project=project, skill=skill)
        ]
        for skill in skills
    }

    if request.method == 'POST':
        form = ProjectForm(request.POST, instance=project, current_project=project)  # Przekazujemy instancję projektu

        if 'suggest_employees' in request.POST:
            # Zbieranie wymagań umiejętności
            skill_requirements_obj = {}  # Słownik z obiektami Skill jako kluczami
            skill_requirements_by_id = {}  # Słownik z ID umiejętności jako kluczami
            for skill in skills:
                required_count = int(request.POST.get(f'required_count_{skill.id}', 0))
                if required_count > 0:
                    skill_requirements_obj[skill] = required_count
                    skill_requirements_by_id[skill.id] = required_count

            # Generowanie sugestii pracowników
            suggested_employees = suggest_team_members_with_annealing(project.id, skill_requirements_obj)
            
            # Sprawdź, czy dla każdej umiejętności znaleziono wystarczającą liczbę pracowników
            skill_counts = {}
            for employee in suggested_employees:
                skill_name = employee['skill']
                skill_counts[skill_name] = skill_counts.get(skill_name, 0) + 1
            
            # Dodaj komunikaty o brakujących pracownikach
            for skill, required_count in skill_requirements_obj.items():
                skill_name = skill.name
                found_count = skill_counts.get(skill_name, 0)
                if found_count < required_count:
                    messages.warning(
                        request, 
                        f"Nie znaleziono wystarczającej liczby pracowników z umiejętnością {skill_name}. "
                        f"Wymagano: {required_count}, znaleziono: {found_count}."
                    )

            # Renderowanie widoku z sugestiami
            return render(request, 'projects/edit_project.html', {
                'form': form,
                'skills': skills,
                'project': project,
                'skill_requirements': skill_requirements_by_id,
                'assigned_employees': assigned_employees,
                'suggested_employees': suggested_employees,
            })

        if form.is_valid():
            project = form.save()

            # Usunięcie istniejących wymagań umiejętności
            ProjectSkillRequirement.objects.filter(project=project).delete()

            # Dodanie nowych wymagań umiejętności
            for skill in skills:
                required_count = int(request.POST.get(f'required_count_{skill.id}', 0))
                if required_count > 0:
                    ProjectSkillRequirement.objects.create(
                    project=project,
                    skill=skill,
                    required_count=required_count
                )

            # Usunięcie istniejących przypisań pracowników
            EmployeeProjectAssignment.objects.filter(project=project).delete()
            project.employees.clear()

            # Przygotowanie słownika z danymi o wymaganiach
            skill_requirements_obj = {}
            for skill in skills:
                required_count = int(request.POST.get(f'required_count_{skill.id}', 0))
                if required_count > 0:
                    skill_requirements_obj[skill] = required_count

            # Automatyczne przypisanie pracowników na podstawie sugerowanej listy
            suggested_employees = suggest_team_members_with_annealing(project.id, skill_requirements_obj)
            for employee in suggested_employees:
                skill_instance = Skill.objects.get(name=employee['skill'])
                project.employees.add(Employee.objects.get(id=employee['employee_id']))
                EmployeeProjectAssignment.objects.create(
                    project=project,
                    employee=Employee.objects.get(id=employee['employee_id']),
                    skill=skill_instance
                )

            messages.success(request, "Projekt został zaktualizowany.")
            return redirect('project_list')
        else:
            messages.error(request, "Formularz zawiera błędy.")

    else:
        form = ProjectForm(instance=project, current_project=project)  # Przekazujemy instancję projektu

    return render(request, 'projects/edit_project.html', {
        'form': form,
        'skills': skills,
        'project': project,
        'skill_requirements': skill_requirements,  # Tutaj już mamy słownik z ID jako kluczami
        'assigned_employees': assigned_employees,
    })

def calculate_team_diversity_score(team_members):
    """
    Oblicza punktację zespołu na podstawie różnorodności ról Belbina oraz poziomu umiejętności.
    
    Punktacja jest obliczana na podstawie:
    1. Liczby różnych kategorii ról (zadaniowe, intelektualne, socjalne)
    2. Liczby różnych konkretnych ról w ramach każdej kategorii
    3. Równomierności rozkładu ról w zespole
    4. Poziomu zaawansowania umiejętności pracowników (junior/mid/senior)
    
    Args:
        team_members: Lista pracowników w zespole (obiekty Employee)
        
    Returns:
        float: Punktacja zespołu (0-100)
    """
    if not team_members:
        return 0.0
    
    # Mapowanie ról na kategorie zgodnie z BELBIN_CATEGORIES
    role_categories = {
        'PO': 'zadaniowe',
        'CZA': 'zadaniowe',
        'PER': 'zadaniowe',
        'SE': 'intelektualne',
        'SIE': 'intelektualne',
        'NG': 'socjalne',
        'CZG': 'socjalne',
        'CZK': 'socjalne'
    }
    
    # Zbieramy role pracowników (tylko te na poziomie 'bardzo wysoki' i 'wysoki')
    roles_by_level = {'bardzo wysoki': [], 'wysoki': []}
    
    for employee in team_members:
        if employee.belbin_test_result and 'roles_by_level' in employee.belbin_test_result:
            for level in ['bardzo wysoki', 'wysoki']:
                roles = employee.belbin_test_result['roles_by_level'].get(level, [])
                roles_by_level[level].extend(roles)
    
    # Policz wystąpienia każdej roli na każdym poziomie
    role_counts = {'bardzo wysoki': {}, 'wysoki': {}}
    for level in ['bardzo wysoki', 'wysoki']:
        for role in roles_by_level[level]:
            role_counts[level][role] = role_counts[level].get(role, 0) + 1
    
    # Policz wystąpienia każdej kategorii na każdym poziomie
    category_counts = {'bardzo wysoki': {}, 'wysoki': {}}
    for level in ['bardzo wysoki', 'wysoki']:
        for role in roles_by_level[level]:
            category = role_categories.get(role)
            if category:
                category_counts[level][category] = category_counts[level].get(category, 0) + 1
    
    # Oblicz punktację za różnorodność
    
    # 1. Punkty za różnorodność kategorii (0-30 punktów)
    # Maksymalna liczba punktów za 3 różne kategorie na poziomie 'bardzo wysoki'
    category_diversity_score = len(category_counts['bardzo wysoki']) * 10.0
    
    # 2. Punkty za różnorodność ról (0-40 punktów)
    # Maksymalna liczba punktów za 8 różnych ról (po 5 punktów za każdą unikalną rolę)
    role_diversity_score = len(role_counts['bardzo wysoki']) * 5.0
    
    # 3. Punkty za równomierność rozkładu (0-30 punktów)
    # Sprawdzamy, czy kategorie są równomiernie reprezentowane
    balance_score = 0.0
    if category_counts['bardzo wysoki']:
        max_category_count = max(category_counts['bardzo wysoki'].values())
        min_category_count = min(category_counts['bardzo wysoki'].values())
        balance_score = 30.0 * (1.0 - (max_category_count - min_category_count) / len(team_members))
    
    # 4. Obliczanie punktacji za poziom umiejętności (0-100 punktów)
    # Punktacja: 12.5 dla senior, 6.25 dla mid, 2.1 dla junior
    skill_level_score = 0.0
    
    for employee in team_members:
        # Pobierz wszystkie umiejętności pracownika z poziomem zaawansowania
        employee_skills = employee.employee_skills.all()
        
        for skill in employee_skills:
            if skill.proficiency_level == '3':  # senior
                skill_level_score += 12.5
            elif skill.proficiency_level == '2':  # mid
                skill_level_score += 6.25
            elif skill.proficiency_level == '1':  # junior
                skill_level_score += 2.1
    
    # Ograniczenie maksymalnej punktacji za umiejętności do 100
    skill_level_score = min(skill_level_score, 100.0)
    
    # Wagi dla poszczególnych składowych
    weights = {
        'diversity': 0.6,  # Waga dla różnorodności ról Belbina
        'skill_level': 0.4  # Waga dla poziomu umiejętności
    }
    
    # Obliczenie łącznej punktacji za różnorodność (max 100 punktów)
    diversity_score = category_diversity_score + role_diversity_score + balance_score
    
    # Obliczenie końcowej punktacji z uwzględnieniem wag
    total_score = (weights['diversity'] * diversity_score) + (weights['skill_level'] * skill_level_score)
    
    # Zwróć punktację zespołu
    return total_score

def generate_neighbor_team(current_team, qualified_employees_by_skill, requirements):
    """
    Generuje sąsiednie rozwiązanie poprzez zamianę jednego pracownika na innego z tą samą umiejętnością.
    
    Args:
        current_team: Obecny zespół (lista pracowników)
        qualified_employees_by_skill: Słownik {skill: [pracownicy]} z kwalifikującymi się pracownikami
        requirements: Słownik {skill: liczba} z wymaganiami projektu
        
    Returns:
        Nowy zespół (lista pracowników)
    """
    # Tworzymy kopię obecnego zespołu
    new_team = deepcopy(current_team)
    
    if not new_team:
        return new_team
    
    # Wybieramy losowego pracownika do zamiany
    index_to_replace = random.randrange(len(new_team))
    employee_to_replace = new_team[index_to_replace]
    
    # Określamy umiejętność zastępowanego pracownika
    employee_skill = None
    for skill, count in requirements.items():
        if skill in employee_to_replace.skills.all():
            employee_skill = skill
            break
    
    if not employee_skill:
        return new_team  # Nie znaleziono umiejętności, zwracamy bez zmian
    
    # Wybieramy losowego pracownika z tą samą umiejętnością
    potential_replacements = [e for e in qualified_employees_by_skill[employee_skill] 
                             if e.id != employee_to_replace.id and e not in new_team and
                             e.belbin_test_result and 'roles_by_level' in e.belbin_test_result]
    
    if not potential_replacements:
        return new_team  # Brak potencjalnych zamienników
    
    # Wybieramy losowego pracownika jako zamiennik
    replacement = random.choice(potential_replacements)
    new_team[index_to_replace] = replacement
    
    return new_team

def simulated_annealing_team_optimization(initial_team, qualified_employees_by_skill, requirements, 
                                         initial_temp=100.0, cooling_rate=0.95, min_temp=0.1, 
                                         iterations_per_temp=20):
    """
    Algorytm symulowanego wyżarzania do optymalizacji doboru zespołu.
    
    Args:
        initial_team: Początkowy zespół (lista pracowników)
        qualified_employees_by_skill: Słownik {skill: [pracownicy]} z kwalifikującymi się pracownikami
        requirements: Słownik {skill: liczba} z wymaganiami projektu
        initial_temp: Początkowa temperatura
        cooling_rate: Współczynnik chłodzenia (0 < cooling_rate < 1)
        min_temp: Minimalna temperatura (warunek zatrzymania)
        iterations_per_temp: Liczba iteracji na każdym poziomie temperatury
        
    Returns:
        Zoptymalizowany zespół (lista pracowników) i jego punktacja
    """
    # Inicjalizacja
    current_team = deepcopy(initial_team)
    best_team = deepcopy(current_team)
    current_score = calculate_team_diversity_score(current_team)
    best_score = current_score
    
    # Główna pętla algorytmu
    temp = initial_temp
    iteration = 0
    
    while temp > min_temp:
        for i in range(iterations_per_temp):
            # Generujemy sąsiednie rozwiązanie
            neighbor_team = generate_neighbor_team(current_team, qualified_employees_by_skill, requirements)
            neighbor_score = calculate_team_diversity_score(neighbor_team)
            
            # Obliczamy zmianę punktacji
            delta_e = neighbor_score - current_score
            
            # Decydujemy, czy zaakceptować nowe rozwiązanie
            if delta_e > 0:  # Lepsze rozwiązanie - zawsze akceptujemy
                current_team = neighbor_team
                current_score = neighbor_score
                
                # Aktualizujemy najlepsze rozwiązanie, jeśli znaleźliśmy lepsze
                if current_score > best_score:
                    best_team = deepcopy(current_team)
                    best_score = current_score
            else:  # Gorsze rozwiązanie - akceptujemy z pewnym prawdopodobieństwem
                # Prawdopodobieństwo akceptacji maleje wraz ze spadkiem temperatury
                # i wzrostem pogorszenia rozwiązania
                acceptance_probability = math.exp(delta_e / temp)
                if random.random() < acceptance_probability:
                    current_team = neighbor_team
                    current_score = neighbor_score
        
        # Obniżamy temperaturę
        temp *= cooling_rate
        iteration += 1
    
    return best_team, best_score

def suggest_team_members_with_annealing(project_id, requirements):
    """
    Sugeruje członków zespołu dla projektu z wykorzystaniem symulowanego wyżarzania.
    
    Args:
        project_id: ID projektu
        requirements: Słownik {skill: liczba} z wymaganiami projektu
        
    Returns:
        Lista sugerowanych pracowników w formacie zgodnym z suggest_team_members
    """
    # Faza 1: Użyj obecnego algorytmu do wygenerowania początkowego zespołu
    initial_suggestions = suggest_team_members(required_skills=requirements, project=None)
    
    # Przekształć sugestie na listę pracowników
    initial_team = []
    employee_ids = set()
    for suggestion in initial_suggestions:
        employee_id = suggestion['employee_id']
        if employee_id not in employee_ids:
            employee = Employee.objects.get(id=employee_id)
            initial_team.append(employee)
            employee_ids.add(employee_id)
    
    # Przygotuj słownik kwalifikujących się pracowników według umiejętności
    qualified_employees_by_skill = {}
    for skill, count in requirements.items():
        qualified = list(Employee.objects.filter(
            skills=skill, 
            belbin_test_result__has_key='roles_by_level'
        ))
        qualified_employees_by_skill[skill] = qualified
    
    # Faza 2: Użyj symulowanego wyżarzania do optymalizacji zespołu
    optimized_team, optimized_score = simulated_annealing_team_optimization(
        initial_team=initial_team,
        qualified_employees_by_skill=qualified_employees_by_skill,
        requirements=requirements,
        initial_temp=100.0,
        cooling_rate=0.95,
        min_temp=0.1,
        iterations_per_temp=20
    )
    
    # Przekształć zoptymalizowany zespół z powrotem na format sugestii
    optimized_suggestions = []
    for employee in optimized_team:
        # Znajdź umiejętność, dla której pracownik został wybrany
        for skill in requirements.keys():
            if skill in employee.skills.all():
                optimized_suggestions.append({
                    'first_name': employee.user.first_name,
                    'last_name': employee.user.last_name,
                    'email': employee.user.email,
                    'skill': skill.name,
                    'employee_id': employee.id
                })
                break
    
    return optimized_suggestions

def calculate_score_components(team_members):
    """
    Oblicza składowe punktacji zespołu na podstawie różnorodności ról Belbina oraz poziomu umiejętności.
    Funkcja pomocnicza używana w testach.
    
    Args:
        team_members: Lista pracowników w zespole (obiekty Employee)
        
    Returns:
        dict: Słownik zawierający składowe punktacji zespołu
    """
    if not team_members:
        return {
            'total_score': 0.0,
            'diversity_score': 0.0,
            'skill_level_score': 0.0,
            'category_diversity_score': 0.0,
            'role_diversity_score': 0.0,
            'balance_score': 0.0,
            'skill_counts': {'1': 0, '2': 0, '3': 0}
        }
    
    # Mapowanie ról na kategorie zgodnie z BELBIN_CATEGORIES
    role_categories = {
        'PO': 'zadaniowe',
        'CZA': 'zadaniowe',
        'PER': 'zadaniowe',
        'SE': 'intelektualne',
        'SIE': 'intelektualne',
        'NG': 'socjalne',
        'CZG': 'socjalne',
        'CZK': 'socjalne'
    }
    
    # Zbieramy role pracowników (tylko te na poziomie 'bardzo wysoki' i 'wysoki')
    roles_by_level = {'bardzo wysoki': [], 'wysoki': []}
    
    for employee in team_members:
        if employee.belbin_test_result and 'roles_by_level' in employee.belbin_test_result:
            for level in ['bardzo wysoki', 'wysoki']:
                roles = employee.belbin_test_result['roles_by_level'].get(level, [])
                roles_by_level[level].extend(roles)
    
    # Policz wystąpienia każdej roli na każdym poziomie
    role_counts = {'bardzo wysoki': {}, 'wysoki': {}}
    for level in ['bardzo wysoki', 'wysoki']:
        for role in roles_by_level[level]:
            role_counts[level][role] = role_counts[level].get(role, 0) + 1
    
    # Policz wystąpienia każdej kategorii na każdym poziomie
    category_counts = {'bardzo wysoki': {}, 'wysoki': {}}
    for level in ['bardzo wysoki', 'wysoki']:
        for role in roles_by_level[level]:
            category = role_categories.get(role)
            if category:
                category_counts[level][category] = category_counts[level].get(category, 0) + 1
    
    # Oblicz punktację za różnorodność
    
    # 1. Punkty za różnorodność kategorii (0-30 punktów)
    # Maksymalna liczba punktów za 3 różne kategorie na poziomie 'bardzo wysoki'
    category_diversity_score = len(category_counts['bardzo wysoki']) * 10.0
    
    # 2. Punkty za różnorodność ról (0-40 punktów)
    # Maksymalna liczba punktów za 8 różnych ról (po 5 punktów za każdą unikalną rolę)
    role_diversity_score = len(role_counts['bardzo wysoki']) * 5.0
    
    # 3. Punkty za równomierność rozkładu (0-30 punktów)
    # Sprawdzamy, czy kategorie są równomiernie reprezentowane
    balance_score = 0.0
    if category_counts['bardzo wysoki']:
        max_category_count = max(category_counts['bardzo wysoki'].values())
        min_category_count = min(category_counts['bardzo wysoki'].values())
        balance_score = 30.0 * (1.0 - (max_category_count - min_category_count) / len(team_members))
    
    # 4. Obliczanie punktacji za poziom umiejętności (0-100 punktów)
    # Punktacja: 12.5 dla senior, 6.25 dla mid, 2.1 dla junior
    skill_level_score = 0.0
    skill_counts = {'1': 0, '2': 0, '3': 0}  # junior, mid, senior
    
    for employee in team_members:
        # Pobierz wszystkie umiejętności pracownika z poziomem zaawansowania
        employee_skills = employee.employee_skills.all()
        
        for skill in employee_skills:
            if skill.proficiency_level == '3':  # senior
                skill_level_score += 12.5
                skill_counts['3'] += 1
            elif skill.proficiency_level == '2':  # mid
                skill_level_score += 6.25
                skill_counts['2'] += 1
            elif skill.proficiency_level == '1':  # junior
                skill_level_score += 2.1
                skill_counts['1'] += 1
    
    # Ograniczenie maksymalnej punktacji za umiejętności do 100
    skill_level_score = min(skill_level_score, 100.0)
    
    # Wagi dla poszczególnych składowych
    weights = {
        'diversity': 0.6,  # Waga dla różnorodności ról Belbina
        'skill_level': 0.4  # Waga dla poziomu umiejętności
    }
    
    # Obliczenie łącznej punktacji za różnorodność (max 100 punktów)
    diversity_score = category_diversity_score + role_diversity_score + balance_score
    
    # Obliczenie końcowej punktacji z uwzględnieniem wag
    total_score = (weights['diversity'] * diversity_score) + (weights['skill_level'] * skill_level_score)
    
    # Zwróć słownik z punktacją i jej składowymi
    return {
        'total_score': total_score,
        'diversity_score': diversity_score,
        'skill_level_score': skill_level_score,
        'category_diversity_score': category_diversity_score,
        'role_diversity_score': role_diversity_score,
        'balance_score': balance_score,
        'skill_counts': skill_counts
    }

def save_employee_skills(request):
    if request.method == 'POST':
        employee = request.user.profile  # Zakładam, że masz profil pracownika powiązany z użytkownikiem
        skills = request.POST.getlist('skills')
        proficiency_levels = request.POST.getlist('proficiency_levels')

        # Zapisz umiejętności i poziomy zaawansowania
        for skill_id, proficiency_level in zip(skills, proficiency_levels):
            skill = Skill.objects.get(id=skill_id)
            EmployeeSkill.objects.update_or_create(
                employee=employee,
                skill=skill,
                defaults={'proficiency_level': proficiency_level}
            )

        messages.success(request, "Umiejętności zostały zaktualizowane.")
        return redirect('profile')  # lub inny widok

def calculate_multicriteria_team_score(team_members, weights=None):
    """
    Oblicza punktację zespołu na podstawie wielu kryteriów z możliwością konfiguracji wag.
    
    Kryteria:
    1. Poziom umiejętności technicznych (junior/mid/senior)
    2. Różnorodność kategorii Belbina (zadaniowe, intelektualne, socjalne)
    3. Liczba różnych ról na poziomie "bardzo wysoki"
    4. Balans zespołu (równomierność rozkładu kategorii)
    
    Args:
        team_members: Lista pracowników w zespole
        weights: Słownik wag dla poszczególnych kryteriów (domyślnie równe wagi)
        
    Returns:
        Ważona punktacja zespołu (float)
    """
    if not team_members:
        return 0.0
    
    # Domyślne wagi (można dostosować)
    if weights is None:
        weights = {
            'skill_level': 0.3,
            'category_diversity': 0.3,
            'role_diversity': 0.2,
            'team_balance': 0.2
        }
    
    # 1. Ocena poziomu umiejętności (0-100)
    skill_level_score = 0
    for employee in team_members:
        for employee_skill in employee.employee_skills.all():
            if employee_skill.proficiency_level == 'senior':
                skill_level_score += 12.5
            elif employee_skill.proficiency_level == 'mid':
                skill_level_score += 6.25
            else:  # junior
                skill_level_score += 2.1
    
    # Normalizacja do przedziału 0-100
    total_skills = sum(1 for employee in team_members for _ in employee.employee_skills.all())
    if total_skills > 0:
        skill_level_score = (skill_level_score / (total_skills * 30)) * 100
    
    # 2 & 3 & 4. Pozostałe komponenty z istniejącej funkcji calculate_team_diversity_score
    # (tutaj kod z Twojej funkcji calculate_team_diversity_score)
    
    # Obliczenie ważonej sumy
    final_score = (
        weights['skill_level'] * skill_level_score +
        weights['category_diversity'] * category_diversity_score +
        weights['role_diversity'] * role_diversity_score +
        weights['team_balance'] * balance_score
    )
    
    return final_score

@login_required
def view_project_details(request, project_id):
    """
    Widok szczegółów projektu dla pracownika. Pracownik może zobaczyć projekt,
    do którego jest przypisany.
    """
    try:
        employee = request.user.employee  # Użyj instancji Employee
    except AttributeError:
        try:
            employee = Employee.objects.get(user=request.user)
            request.user.employee = employee
        except Employee.DoesNotExist:
            messages.error(request, 'Nie znaleziono profilu pracownika.')
            return redirect('profile')
    
    project = get_object_or_404(Project, id=project_id)
    is_assigned = project.employeeprojectassignment_set.filter(employee=employee).exists()
    
    if not is_assigned and not request.user.is_staff:
        messages.error(request, 'Nie masz dostępu do tego projektu.')
        return redirect('my_profile')

    # Obsługa formularza wiadomości
    message_form = ProjectMessageForm()  # Inicjalizuj formularz na początku
    if request.method == 'POST':
        message_form = ProjectMessageForm(request.POST)
        if message_form.is_valid():
            message = message_form.save(commit=False)
            message.project = project
            message.user = employee  # Użyj instancji Employee
            message.save()
            messages.success(request, 'Wiadomość została dodana.')
            return redirect('view_project_details', project_id=project.id)

    # Pobierz wszystkie wiadomości dla projektu
    messages_list = project.messages.all()  

    return render(request, 'projects/project_details.html', {
        'project': project,
        'message_form': message_form,
        'messages': messages_list,  # Użyj zmiennej messages_list
    })

@login_required
def delete_message(request, message_id):
    """Widok do usuwania wiadomości."""
    message = get_object_or_404(ProjectMessage, id=message_id)

    # Sprawdź, czy użytkownik jest właścicielem wiadomości
    if message.user != request.user.employee:
        messages.error(request, 'Nie masz uprawnień do usunięcia tej wiadomości.')
        return redirect('view_project_details', project_id=message.project.id)

    message.delete()
    messages.success(request, 'Wiadomość została usunięta.')
    return redirect('view_project_details', project_id=message.project.id)
