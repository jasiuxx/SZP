from django.shortcuts import render, redirect
from django.contrib.auth import login
from .forms import UserRegistrationForm
from employees.forms import EditSkillsForm
from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from employees.models import Employee, EmployeeSkill, Skill
from django.contrib import messages

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
            employee = Employee.objects.get(user=request.user)
            request.user.employee = employee  # Dodajemy atrybut employee do obiektu użytkownika
            
            # Pobierz poziomy zaawansowania dla wszystkich umiejętności pracownika
            skill_levels = {}
            for employee_skill in EmployeeSkill.objects.filter(employee=employee):
                skill_levels[str(employee_skill.skill.id)] = employee_skill.proficiency_level
            
            if request.method == 'POST':
                print(f"DEBUG - POST data: {request.POST}")  # Dodajemy debugowanie
                
                # Pobierz zaznaczone umiejętności
                selected_skill_ids = request.POST.getlist('skills')
                print(f"DEBUG - Selected skill IDs: {selected_skill_ids}")
                
                # Pobierz obiekty Skill dla zaznaczonych umiejętności
                selected_skills = Skill.objects.filter(id__in=selected_skill_ids)
                print(f"DEBUG - Selected skills: {list(selected_skills.values())}")
                
                # Zapisz wybrane umiejętności do pracownika
                employee.skills.set(selected_skills)
                
                # Usuń wszystkie istniejące rekordy EmployeeSkill dla tego pracownika
                EmployeeSkill.objects.filter(employee=employee).delete()
                
                # Zapisz poziomy zaawansowania dla wybranych umiejętności
                for skill_id in selected_skill_ids:
                    proficiency_level = request.POST.get(f'proficiency_level_{skill_id}')
                    print(f"DEBUG - Saving skill {skill_id} with level: {proficiency_level}")
                    
                    if proficiency_level:
                        try:
                            skill = Skill.objects.get(id=skill_id)
                            employee_skill = EmployeeSkill.objects.create(
                                employee=employee,
                                skill=skill,
                                proficiency_level=proficiency_level
                            )
                            print(f"DEBUG - Created EmployeeSkill: {employee_skill.id}, level: {employee_skill.proficiency_level}")
                        except Exception as e:
                            print(f"DEBUG - Error saving EmployeeSkill: {e}")
                
                # Sprawdź, czy poziomy zaawansowania zostały zapisane
                saved_skills = EmployeeSkill.objects.filter(employee=employee)
                print(f"DEBUG - Saved skills after save: {list(saved_skills.values())}")
                
                # Odśwież stronę profilu z komunikatem
                messages.success(request, "Umiejętności zostały zaktualizowane.")
                
                # Zamiast przekierowania, od razu renderuj stronę z aktualnymi danymi
                # Pobierz ponownie poziomy zaawansowania
                skill_levels = {}
                for employee_skill in EmployeeSkill.objects.filter(employee=employee):
                    skill_levels[str(employee_skill.skill.id)] = employee_skill.proficiency_level
                
                print(f"DEBUG - Updated Skill Levels: {skill_levels}")  # Dodajemy debugowanie
                
                # Utwórz formularz z aktualnymi danymi
                form = EditSkillsForm(instance=employee)
                
                return render(request, 'account/profile.html', {
                    'first_name': request.user.first_name,
                    'last_name': request.user.last_name,
                    'email': request.user.email,
                    'form': form,
                    'skill_levels': skill_levels,
                    'employee': employee  # Dodajemy obiekt pracownika do kontekstu
                })
            
            # Utwórz formularz
            form = EditSkillsForm(instance=employee)
            
            return render(request, 'account/profile.html', {
                'first_name': request.user.first_name,
                'last_name': request.user.last_name,
                'email': request.user.email,
                'form': form,
                'skill_levels': skill_levels,
                'employee': employee  # Dodajemy obiekt pracownika do kontekstu
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
