import random
from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from employees.models import Employee, Skill
from projects.models import Project, ProjectSkillRequirement

User = get_user_model()

class Command(BaseCommand):
    help = 'Generuje dane testowe dla algorytmu sugerowania pracowników'

    def add_arguments(self, parser):
        parser.add_argument('--employees', type=int, default=20, help='Liczba pracowników do wygenerowania')
        parser.add_argument('--skills', type=int, default=10, help='Liczba umiejętności do wygenerowania')
        parser.add_argument('--clear', action='store_true', help='Wyczyść istniejące dane testowe')

    def handle(self, *args, **options):
        if options['clear']:
            self.clear_test_data()
            self.stdout.write(self.style.SUCCESS('Wyczyszczono istniejące dane testowe'))
        
        num_employees = options['employees']
        num_skills = options['skills']
        
        # Generowanie umiejętności
        skills = self.generate_skills(num_skills)
        self.stdout.write(self.style.SUCCESS(f'Wygenerowano {len(skills)} umiejętności'))
        
        # Generowanie pracowników
        employees = self.generate_employees(num_employees, skills)
        self.stdout.write(self.style.SUCCESS(f'Wygenerowano {len(employees)} pracowników'))
        
        self.stdout.write(self.style.SUCCESS('Generowanie danych testowych zakończone'))
    
    def clear_test_data(self):
        # Usuwanie pracowników testowych
        User.objects.filter(username__startswith='test_').delete()
        # Usuwanie umiejętności testowych
        Skill.objects.filter(name__startswith='Test_').delete()
    
    def generate_skills(self, num_skills):
        skills = []
        existing_skills = list(Skill.objects.all())
        
        # Jeśli mamy już wystarczająco dużo umiejętności, używamy istniejących
        if len(existing_skills) >= num_skills:
            return existing_skills[:num_skills]
        
        # Dodajemy brakujące umiejętności
        skills_to_create = num_skills - len(existing_skills)
        skill_names = [
            'Python', 'Django', 'JavaScript', 'React', 'Angular', 'Vue.js',
            'Java', 'Spring', 'C#', '.NET', 'PHP', 'Laravel', 'Ruby', 'Rails',
            'Go', 'Rust', 'C++', 'Swift', 'Kotlin', 'Flutter', 'SQL', 'NoSQL',
            'MongoDB', 'PostgreSQL', 'MySQL', 'DevOps', 'Docker', 'Kubernetes',
            'AWS', 'Azure', 'GCP', 'Machine Learning', 'Data Science', 'AI',
            'Mobile Development', 'Web Development', 'UI/UX Design', 'Project Management'
        ]
        
        # Filtrujemy nazwy umiejętności, które już istnieją
        existing_names = {skill.name for skill in existing_skills}
        available_names = [name for name in skill_names if name not in existing_names]
        
        # Jeśli brakuje nazw, generujemy dodatkowe
        if len(available_names) < skills_to_create:
            for i in range(skills_to_create - len(available_names)):
                available_names.append(f'Test_Skill_{i+1}')
        
        # Tworzymy nowe umiejętności
        for i in range(skills_to_create):
            if i < len(available_names):
                skill = Skill.objects.create(name=available_names[i])
                skills.append(skill)
        
        return existing_skills + skills
    
    def generate_employees(self, num_employees, skills):
        employees = []
        
        # Role Belbina
        belbin_roles = {
            'socjalne': ['NG', 'CZG', 'CZK'],
            'intelektualne': ['SE', 'SIE'],
            'zadaniowe': ['PO', 'CZA', 'PER']
        }
        
        # Poziomy ról
        levels = ['bardzo wysoki', 'wysoki', 'średni', 'niski']
        
        # Imiona i nazwiska
        first_names = [
            'Jan', 'Anna', 'Piotr', 'Maria', 'Krzysztof', 'Katarzyna', 'Andrzej', 'Małgorzata',
            'Marek', 'Agnieszka', 'Tomasz', 'Barbara', 'Paweł', 'Ewa', 'Michał', 'Zofia',
            'Stanisław', 'Elżbieta', 'Jakub', 'Magdalena'
        ]
        
        last_names = [
            'Nowak', 'Kowalski', 'Wiśniewski', 'Wójcik', 'Kowalczyk', 'Kamiński', 'Lewandowski',
            'Zieliński', 'Szymański', 'Woźniak', 'Dąbrowski', 'Kozłowski', 'Jankowski', 'Mazur',
            'Kwiatkowski', 'Krawczyk', 'Piotrowski', 'Grabowski', 'Nowakowski', 'Pawłowski'
        ]
        
        # Generowanie pracowników
        for i in range(num_employees):
            # Losowe imię i nazwisko
            first_name = random.choice(first_names)
            last_name = random.choice(last_names)
            username = f'test_emp_{i+1}'
            email = f'{username}@example.com'
            
            # Tworzenie użytkownika
            user = User.objects.create_user(
                username=username,
                email=email,
                password='password',
                first_name=first_name,
                last_name=last_name,
                is_employee=True
            )
            
            # Generowanie ról Belbina
            roles_by_level = {}
            all_roles = [role for roles in belbin_roles.values() for role in roles]
            
            # Losujemy 1-2 role dla poziomu 'bardzo wysoki'
            very_high_roles = random.sample(all_roles, random.randint(1, 2))
            roles_by_level['bardzo wysoki'] = very_high_roles
            
            # Losujemy 1-2 role dla poziomu 'wysoki' (różne od 'bardzo wysoki')
            remaining_roles = [role for role in all_roles if role not in very_high_roles]
            high_roles = random.sample(remaining_roles, min(random.randint(1, 2), len(remaining_roles)))
            roles_by_level['wysoki'] = high_roles
            
            # Losujemy 1-3 role dla poziomu 'średni' (różne od 'bardzo wysoki' i 'wysoki')
            remaining_roles = [role for role in remaining_roles if role not in high_roles]
            medium_roles = random.sample(remaining_roles, min(random.randint(1, 3), len(remaining_roles)))
            roles_by_level['średni'] = medium_roles
            
            # Tworzenie pracownika
            employee = Employee.objects.create(
                user=user,
                belbin_test_result={'roles_by_level': roles_by_level}
            )
            
            # Przypisanie losowych umiejętności (2-4)
            num_skills = random.randint(2, 4)
            selected_skills = random.sample(skills, min(num_skills, len(skills)))
            for skill in selected_skills:
                employee.skills.add(skill)
            
            employees.append(employee)
        
        return employees 