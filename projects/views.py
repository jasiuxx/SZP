from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.db import transaction
from django.http import Http404
from django.views import View
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages

from employers.models import Employer
from .forms import ProjectForm, TestAlgorithmForm
from .models import Project, Skill, ProjectSkillRequirement, EmployeeProjectAssignment
from employees.models import Employee

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
            suggested_employees = suggest_team_members(skill_requirements)
            
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
            suggested_employees = suggest_team_members(skill_requirements, project)
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
            suggested_employees = suggest_team_members(skill_requirements_obj, project)
            
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
            suggested_employees = suggest_team_members(skill_requirements_obj, project)
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




def test_suggest_team_members():
    """
    Funkcja testowa do sprawdzenia działania algorytmu sugerowania pracowników.
    """
    from django.contrib.auth import get_user_model
    User = get_user_model()

    # 1. Przygotowanie danych testowych
    def create_test_employee(username, first_name, roles_by_level, skills):
        user = User.objects.create(
            username=username,
            first_name=first_name,
            is_employee=True
        )
        employee = Employee.objects.create(
            user=user,
            belbin_test_result={'roles_by_level': roles_by_level}
        )
        for skill in skills:
            employee.skills.add(skill)
        return employee

    # Wyczyść stare dane testowe
    Employee.objects.filter(user__username__startswith='test_').delete()
    User.objects.filter(username__startswith='test_').delete()

    # Stwórz umiejętności testowe
    python_skill = Skill.objects.get_or_create(name='Python')[0]
    django_skill = Skill.objects.get_or_create(name='Django')[0]
    js_skill = Skill.objects.get_or_create(name='JavaScript')[0]

    # Stwórz pracowników testowych
    employees = [
        # Python developer z wysokim PO (zadaniowe)
        create_test_employee(
            'test_emp1', 
            'Adam',
            {
                'bardzo wysoki': ['PO'],
                'wysoki': ['CZG'],
                'średni': ['SE']
            },
            [python_skill]
        ),
        # Python/Django developer z bardzo wysokim SE (intelektualne)
        create_test_employee(
            'test_emp2',
            'Barbara',
            {
                'bardzo wysoki': ['SE'],
                'wysoki': ['CZK'],
                'średni': ['PO']
            },
            [python_skill, django_skill]
        ),
        # JavaScript developer z bardzo wysokim CZG (socjalne)
        create_test_employee(
            'test_emp3',
            'Celina',
            {
                'bardzo wysoki': ['CZG'],
                'wysoki': ['PER'],
                'średni': ['SE']
            },
            [js_skill]
        ),
        # Python/Django developer bez testu Belbina
        create_test_employee(
            'test_emp4',
            'Daniel',
            {},
            [python_skill, django_skill]
        ),
    ]

    # 2. Testowe scenariusze
    test_cases = [
        {
            'name': "Test 1: Jeden Python developer",
            'requirements': {python_skill: 1},
            'expected_count': 1
        },
        {
            'name': "Test 2: Dwóch Python developerów",
            'requirements': {python_skill: 2},
            'expected_count': 2
        },
        {
            'name': "Test 3: Python i JavaScript",
            'requirements': {python_skill: 1, js_skill: 1},
            'expected_count': 2
        },
        {
            'name': "Test 4: Więcej niż dostępnych pracowników",
            'requirements': {python_skill: 5},
            'expected_count': 3  # bo mamy tylko 3 Python developerów
        }
    ]

    # 3. Uruchomienie testów
    print("\nRozpoczynam testy algorytmu suggest_team_members:\n")
    
    for test_case in test_cases:
        print(f"\n{test_case['name']}")
        print("-" * 50)
        
        suggested = suggest_team_members(test_case['requirements'])
        
        print(f"Wymagano: {test_case['requirements']}")
        print(f"Znaleziono {len(suggested)} pracowników:")
        
        for emp in suggested:
            print(f"- {emp['first_name']} ({emp['skill']})")
            
        if len(suggested) == test_case['expected_count']:
            print("✓ Test passed")
        else:
            print(f"✗ Test failed: oczekiwano {test_case['expected_count']}, otrzymano {len(suggested)}")
            
        # Sprawdź czy nie ma duplikatów
        employee_ids = [emp['employee_id'] for emp in suggested]
        if len(employee_ids) == len(set(employee_ids)):
            print("✓ Brak duplikatów")
        else:
            print("✗ Znaleziono duplikaty!")

    print("\nTesty zakończone.")

# Możesz uruchomić testy dodając na końcu widoku:
@login_required
def test_algorithm(request):
    if not request.user.is_superuser:
        messages.error(request, "Tylko administrator może uruchomić testy.")
        return redirect('home')
        
    test_suggest_team_members()
    messages.success(request, "Testy zostały wykonane. Sprawdź konsolę po szczegóły.")
    return redirect('home')

@login_required
def test_algorithm_view(request):
    """
    Widok do testowania algorytmu sugerowania pracowników.
    Dostępny tylko dla administratorów.
    """
    if not request.user.is_superuser:
        messages.error(request, "Tylko administrator może uruchomić testy.")
        return redirect('home')
    
    test_results = None
    
    if request.method == 'POST':
        form = TestAlgorithmForm(request.POST)
        if form.is_valid():
            # Pobierz wymagania z formularza
            requirements = {}
            for skill_id, count in form.cleaned_data.items():
                if skill_id.startswith('skill_') and count > 0:
                    skill_id = int(skill_id.replace('skill_', ''))
                    skill = Skill.objects.get(id=skill_id)
                    requirements[skill] = count
            
            # Uruchom algorytm
            suggested = suggest_team_members(requirements)
            
            # Przygotuj wyniki do wyświetlenia
            team_details = []
            skill_counts = {}
            
            # Pobierz obiekty Employee dla sugerowanych pracowników
            employee_ids = [emp['employee_id'] for emp in suggested]
            team_members = Employee.objects.filter(id__in=employee_ids)
            
            # Oblicz punktację zespołu
            team_score = calculate_team_diversity_score(team_members)
            
            for emp in suggested:
                employee = Employee.objects.get(id=emp['employee_id'])
                skill_name = emp['skill']
                
                # Zliczaj umiejętności
                skill_counts[skill_name] = skill_counts.get(skill_name, 0) + 1
                
                # Przygotuj szczegóły pracownika
                roles = []
                if employee.belbin_test_result:
                    roles_by_level = employee.belbin_test_result.get('roles_by_level', {})
                    for level in ['bardzo wysoki', 'wysoki', 'średni']:
                        for role in roles_by_level.get(level, []):
                            roles.append(f"{role} ({level})")
                
                team_details.append({
                    'name': f"{employee.user.first_name} {employee.user.last_name}",
                    'skill': skill_name,
                    'roles': roles,
                    'all_skills': [s.name for s in employee.skills.all()]
                })
            
            # Analiza ról Belbina w zespole
            role_analysis = {}
            for level in ['bardzo wysoki', 'wysoki', 'średni']:
                role_analysis[level] = {}
            
            for employee in team_members:
                if employee.belbin_test_result:
                    roles_by_level = employee.belbin_test_result.get('roles_by_level', {})
                    for level in ['bardzo wysoki', 'wysoki', 'średni']:
                        for role in roles_by_level.get(level, []):
                            role_analysis[level][role] = role_analysis[level].get(role, 0) + 1
            
            # Mapowanie ról na kategorie
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
            
            # Analiza kategorii ról w zespole
            category_analysis = {'bardzo wysoki': {}, 'wysoki': {}, 'średni': {}}
            for level in ['bardzo wysoki', 'wysoki', 'średni']:
                for role, count in role_analysis[level].items():
                    category = role_categories.get(role)
                    if category:
                        category_analysis[level][category] = category_analysis[level].get(category, 0) + count
            
            test_results = {
                'requirements': {skill.name: count for skill, count in requirements.items()},
                'suggested': suggested,
                'skill_counts': skill_counts,
                'team_score': team_score,
                'role_analysis': role_analysis,
                'category_analysis': category_analysis,
                'team_details': team_details
            }
    else:
        form = TestAlgorithmForm()
        
        # Przygotuj pola formularza dla wszystkich umiejętności
        for skill in Skill.objects.all():
            form.fields[f'skill_{skill.id}'] = forms.IntegerField(
                label=skill.name,
                required=False,
                min_value=0,
                initial=0,
                widget=forms.NumberInput(attrs={'class': 'form-control'})
            )
    
    return render(request, 'projects/test_algorithm.html', {
        'form': form,
        'test_results': test_results
    })

def calculate_team_diversity_score(team_members):
    """
    Oblicza punktację zespołu na podstawie różnorodności ról Belbina.
    
    Punktacja jest obliczana na podstawie:
    1. Liczby różnych kategorii ról (zadaniowe, intelektualne, socjalne)
    2. Liczby różnych konkretnych ról w ramach każdej kategorii
    3. Równomierności rozkładu ról w zespole
    
    Args:
        team_members: Lista pracowników w zespole (obiekty Employee)
        
    Returns:
        Punktacja zespołu (float)
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
    
    # Oblicz punktację
    score = 0.0
    
    # 1. Punkty za różnorodność kategorii (0-30 punktów)
    # Maksymalna liczba punktów za 3 różne kategorie na poziomie 'bardzo wysoki'
    category_diversity_score = len(category_counts['bardzo wysoki']) * 10.0
    score += category_diversity_score
    
    # 2. Punkty za różnorodność ról (0-40 punktów)
    # Maksymalna liczba punktów za 8 różnych ról (po 5 punktów za każdą unikalną rolę)
    role_diversity_score = len(role_counts['bardzo wysoki']) * 5.0
    score += role_diversity_score
    
    # 3. Punkty za równomierność rozkładu (0-30 punktów)
    # Sprawdzamy, czy kategorie są równomiernie reprezentowane
    if category_counts['bardzo wysoki']:
        max_category_count = max(category_counts['bardzo wysoki'].values())
        min_category_count = min(category_counts['bardzo wysoki'].values())
        balance_score = 30.0 * (1.0 - (max_category_count - min_category_count) / len(team_members))
        score += balance_score
    
    return score

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
        
        # Zmniejszamy temperaturę
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

def test_suggest_team_members_with_annealing(requirements_list=None, repetitions=5):
    """
    Testuje algorytm symulowanego wyżarzania i porównuje go z obecnym algorytmem i losowym wyborem.
    
    Args:
        requirements_list: Lista słowników z wymaganiami do przetestowania
        repetitions: Liczba powtórzeń każdego testu
        
    Returns:
        Wyniki testów
    """
    from django.db import connection
    
    # Domyślne wymagania do testowania, jeśli nie podano
    if requirements_list is None:
        # Pobierz dostępne umiejętności
        all_skills = list(Skill.objects.all())
        
        if len(all_skills) < 2:
            print("Za mało umiejętności w bazie danych. Potrzebne są co najmniej 2 umiejętności.")
            return []
        
        # Wybierz umiejętności do testów
        python_skill = next((s for s in all_skills if s.name.lower() == 'python'), all_skills[0])
        js_skill = next((s for s in all_skills if s.name.lower() in ['javascript', 'js']), 
                        all_skills[1] if len(all_skills) > 1 else all_skills[0])
        
        # Pozostałe umiejętności (jeśli dostępne)
        remaining_skills = [s for s in all_skills if s != python_skill and s != js_skill]
        
        # Lista różnych konfiguracji wymagań do przetestowania
        requirements_list = [
            # Test 1: Prosta konfiguracja - tylko pierwsza umiejętność
            {python_skill: 3}
        ]
        
        # Dodaj test z dwiema umiejętnościami, jeśli dostępne
        if len(all_skills) >= 2:
            requirements_list.append({python_skill: 2, js_skill: 2})
        
        # Dodaj bardziej złożone testy, jeśli dostępne więcej umiejętności
        if len(remaining_skills) >= 2:
            requirements_list.append({
                python_skill: 3, 
                js_skill: 2, 
                remaining_skills[0]: 2, 
                remaining_skills[1]: 1
            })
            
            if len(remaining_skills) >= 3:
                requirements_list.append({
                    python_skill: 2, 
                    remaining_skills[0]: 3
                })
                
                requirements_list.append({
                    python_skill: 2, 
                    js_skill: 2, 
                    remaining_skills[0]: 2, 
                    remaining_skills[1]: 2
                })
    
    results = []
    
    # Dla każdej konfiguracji wymagań
    for i, requirements in enumerate(requirements_list):
        print(f"\n=== TEST {i+1}: {requirements} ===\n")
        
        test_results = {
            'requirements': requirements,
            'repetitions': [],
            'algorithm_wins': 0,
            'annealing_wins': 0,
            'random_wins': 0,
            'algorithm_annealing_ties': 0,
            'algorithm_random_ties': 0,
            'annealing_random_ties': 0,
            'all_ties': 0
        }
        
        # Powtórz test kilka razy
        for rep in range(repetitions):
            # 1. Zespół utworzony przez obecny algorytm
            algorithm_team_members = []
            algorithm_suggestions = suggest_team_members(required_skills=requirements, project=None)
            
            employee_ids = set()
            for suggestion in algorithm_suggestions:
                employee_id = suggestion['employee_id']
                if employee_id not in employee_ids:
                    employee = Employee.objects.get(id=employee_id)
                    algorithm_team_members.append(employee)
                    employee_ids.add(employee_id)
            
            algorithm_score = calculate_team_diversity_score(algorithm_team_members)
            
            # 2. Zespół utworzony przez algorytm symulowanego wyżarzania
            annealing_suggestions = suggest_team_members_with_annealing(project_id=None, requirements=requirements)
            
            annealing_team_members = []
            employee_ids = set()
            for suggestion in annealing_suggestions:
                employee_id = suggestion['employee_id']
                if employee_id not in employee_ids:
                    employee = Employee.objects.get(id=employee_id)
                    annealing_team_members.append(employee)
                    employee_ids.add(employee_id)
            
            annealing_score = calculate_team_diversity_score(annealing_team_members)
            
            # 3. Zespół utworzony losowo
            random_team_members = []
            
            # Pobierz wszystkich pracowników z wymaganymi umiejętnościami i z testem Belbina
            all_qualified_employees = {}
            for skill, count in requirements.items():
                # Najpierw pobierz wszystkich pracowników z daną umiejętnością
                all_with_skill = Employee.objects.filter(skills=skill)
                
                # Następnie ręcznie filtruj, aby upewnić się, że mają test Belbina
                qualified = []
                for emp in all_with_skill:
                    if emp.belbin_test_result and 'roles_by_level' in emp.belbin_test_result:
                        if any(emp.belbin_test_result['roles_by_level'].get(level, []) for level in ['bardzo wysoki', 'wysoki']):
                            qualified.append(emp)
                
                all_qualified_employees[skill] = qualified
            
            # Losowo wybierz pracowników dla każdej umiejętności
            for skill, count in requirements.items():
                qualified = all_qualified_employees[skill]
                # Losowo wybierz pracowników, ale nie więcej niż dostępnych
                to_select = min(count, len(qualified))
                if to_select > 0:  # Upewnij się, że jest co wybierać
                    selected = random.sample(qualified, to_select)
                    
                    for employee in selected:
                        if employee not in random_team_members:
                            random_team_members.append(employee)
            
            random_score = calculate_team_diversity_score(random_team_members)
            
            # Określ zwycięzcę
            winner = None
            if algorithm_score > annealing_score and algorithm_score > random_score:
                winner = 'algorithm'
                test_results['algorithm_wins'] += 1
            elif annealing_score > algorithm_score and annealing_score > random_score:
                winner = 'annealing'
                test_results['annealing_wins'] += 1
            elif random_score > algorithm_score and random_score > annealing_score:
                winner = 'random'
                test_results['random_wins'] += 1
            elif algorithm_score == annealing_score and algorithm_score > random_score:
                winner = 'algorithm_annealing_tie'
                test_results['algorithm_annealing_ties'] += 1
            elif algorithm_score == random_score and algorithm_score > annealing_score:
                winner = 'algorithm_random_tie'
                test_results['algorithm_random_ties'] += 1
            elif annealing_score == random_score and annealing_score > algorithm_score:
                winner = 'annealing_random_tie'
                test_results['annealing_random_ties'] += 1
            else:
                winner = 'all_tie'
                test_results['all_ties'] += 1
            
            # Zapisz wyniki tej powtórki
            repetition_result = {
                'algorithm_team': [{'id': e.id, 'name': f"{e.user.first_name} {e.user.last_name}"} for e in algorithm_team_members],
                'algorithm_score': algorithm_score,
                'annealing_team': [{'id': e.id, 'name': f"{e.user.first_name} {e.user.last_name}"} for e in annealing_team_members],
                'annealing_score': annealing_score,
                'random_team': [{'id': e.id, 'name': f"{e.user.first_name} {e.user.last_name}"} for e in random_team_members],
                'random_score': random_score,
                'winner': winner
            }
            test_results['repetitions'].append(repetition_result)
            
            # Wyświetl wyniki tej powtórki
            print(f"Powtórka {rep+1}:")
            print(f"Algorytm: {len(algorithm_team_members)} pracowników, punktacja: {algorithm_score:.2f}")
            print(f"Wyżarzanie: {len(annealing_team_members)} pracowników, punktacja: {annealing_score:.2f}")
            print(f"Losowo: {len(random_team_members)} pracowników, punktacja: {random_score:.2f}")
            print(f"Zwycięzca: {winner}")
            print()
        
        # Oblicz statystyki dla tej konfiguracji
        total_reps = repetitions
        test_results['algorithm_win_rate'] = test_results['algorithm_wins'] / total_reps
        test_results['annealing_win_rate'] = test_results['annealing_wins'] / total_reps
        test_results['random_win_rate'] = test_results['random_wins'] / total_reps
        
        test_results['avg_algorithm_score'] = sum(r['algorithm_score'] for r in test_results['repetitions']) / total_reps
        test_results['avg_annealing_score'] = sum(r['annealing_score'] for r in test_results['repetitions']) / total_reps
        test_results['avg_random_score'] = sum(r['random_score'] for r in test_results['repetitions']) / total_reps
        
        # Wyświetl statystyki
        print(f"=== STATYSTYKI DLA TESTU {i+1} ===")
        print(f"Algorytm wygrywa: {test_results['algorithm_wins']}/{total_reps} ({test_results['algorithm_win_rate']*100:.1f}%)")
        print(f"Wyżarzanie wygrywa: {test_results['annealing_wins']}/{total_reps} ({test_results['annealing_win_rate']*100:.1f}%)")
        print(f"Losowy wybór wygrywa: {test_results['random_wins']}/{total_reps} ({test_results['random_win_rate']*100:.1f}%)")
        print(f"Średnia punktacja algorytmu: {test_results['avg_algorithm_score']:.2f}")
        print(f"Średnia punktacja wyżarzania: {test_results['avg_annealing_score']:.2f}")
        print(f"Średnia punktacja losowego wyboru: {test_results['avg_random_score']:.2f}")
        print()
        
        results.append(test_results)
    
    # Oblicz ogólne statystyki
    total_tests = len(requirements_list) * repetitions
    total_algorithm_wins = sum(r['algorithm_wins'] for r in results)
    total_annealing_wins = sum(r['annealing_wins'] for r in results)
    total_random_wins = sum(r['random_wins'] for r in results)
    
    avg_algorithm_score = sum(r['avg_algorithm_score'] for r in results) / len(results)
    avg_annealing_score = sum(r['avg_annealing_score'] for r in results) / len(results)
    avg_random_score = sum(r['avg_random_score'] for r in results) / len(results)
    
    print("=== PODSUMOWANIE ===")
    print(f"Łączna liczba testów: {total_tests}")
    print(f"Algorytm wygrywa: {total_algorithm_wins}/{total_tests} ({total_algorithm_wins/total_tests*100:.1f}%)")
    print(f"Wyżarzanie wygrywa: {total_annealing_wins}/{total_tests} ({total_annealing_wins/total_tests*100:.1f}%)")
    print(f"Losowy wybór wygrywa: {total_random_wins}/{total_tests} ({total_random_wins/total_tests*100:.1f}%)")
    print(f"Średnia punktacja algorytmu: {avg_algorithm_score:.2f}")
    print(f"Średnia punktacja wyżarzania: {avg_annealing_score:.2f}")
    print(f"Średnia punktacja losowego wyboru: {avg_random_score:.2f}")
    
    return results
