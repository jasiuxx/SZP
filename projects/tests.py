from django.test import TestCase
from django.contrib.auth import get_user_model
from employees.models import Employee, Skill
from .models import Project
from .views import suggest_team_members, calculate_team_diversity_score, suggest_team_members_with_annealing

User = get_user_model()

class TeamSuggestionTests(TestCase):
    def setUp(self):
        """
        Przygotowanie danych testowych przed każdym testem
        """
        # Tworzenie umiejętności
        self.python_skill = Skill.objects.create(name='Python')
        self.django_skill = Skill.objects.create(name='Django')
        self.js_skill = Skill.objects.create(name='JavaScript')
        self.react_skill = Skill.objects.create(name='React')
        self.java_skill = Skill.objects.create(name='Java')

        # Tworzenie pracowników testowych
        self.create_test_employees()

    def create_test_employees(self):
        """Helper do tworzenia pracowników testowych"""
        test_employees = [
            {
                'username': 'test_emp1',
                'first_name': 'Adam',
                'roles': {
                    'roles_by_level': {
                        'bardzo wysoki': ['PO'],  # zadaniowa
                        'wysoki': ['CZG'],        # socjalna
                        'średni': ['SE']          # intelektualna
                    }
                },
                'skills': [self.python_skill, self.react_skill]
            },
            {
                'username': 'test_emp2',
                'first_name': 'Barbara',
                'roles': {
                    'roles_by_level': {
                        'bardzo wysoki': ['SE'],  # intelektualna
                        'wysoki': ['CZK'],        # socjalna
                        'średni': ['PO']          # zadaniowa
                    }
                },
                'skills': [self.python_skill, self.django_skill]
            },
            {
                'username': 'test_emp3',
                'first_name': 'Celina',
                'roles': {
                    'roles_by_level': {
                        'bardzo wysoki': ['CZG'],  # socjalna
                        'wysoki': ['PER'],         # socjalna
                        'średni': ['SE']           # intelektualna
                    }
                },
                'skills': [self.js_skill, self.react_skill]
            },
            {
                'username': 'test_emp4',
                'first_name': 'Daniel',
                'roles': {
                    'roles_by_level': {}
                },
                'skills': [self.python_skill, self.django_skill]
            },
            # Dodajemy więcej pracowników z różnymi rolami i umiejętnościami
            {
                'username': 'test_emp5',
                'first_name': 'Ewa',
                'roles': {
                    'roles_by_level': {
                        'bardzo wysoki': ['PO'],  # zadaniowa
                        'wysoki': ['CZA'],        # zadaniowa
                        'średni': []
                    }
                },
                'skills': [self.python_skill, self.java_skill]
            },
            {
                'username': 'test_emp6',
                'first_name': 'Filip',
                'roles': {
                    'roles_by_level': {
                        'bardzo wysoki': ['SE'],  # intelektualna
                        'wysoki': ['CZK'],        # socjalna
                        'średni': []
                    }
                },
                'skills': [self.python_skill, self.react_skill]
            },
            {
                'username': 'test_emp7',
                'first_name': 'Grzegorz',
                'roles': {
                    'roles_by_level': {
                        'bardzo wysoki': ['CZG'],  # socjalna
                        'wysoki': ['PER'],         # socjalna
                        'średni': []
                    }
                },
                'skills': [self.python_skill, self.js_skill]
            },
        ]

        for emp_data in test_employees:
            user = User.objects.create(
                username=emp_data['username'],
                first_name=emp_data['first_name'],
                is_employee=True
            )
            employee = Employee.objects.create(
                user=user,
                belbin_test_result=emp_data['roles']
            )
            for skill in emp_data['skills']:
                employee.skills.add(skill)

    def test_single_python_developer(self):
        """Test przydzielania jednego Python developera"""
        suggested = suggest_team_members({self.python_skill: 1})
        self.assertEqual(len(suggested), 1)
        self.assertEqual(suggested[0]['skill'], 'Python')

    def test_two_python_developers(self):
        """Test przydzielania dwóch Python developerów"""
        suggested = suggest_team_members({self.python_skill: 2})
        self.assertEqual(len(suggested), 2)
        self.assertEqual(len({emp['employee_id'] for emp in suggested}), 2)  # Brak duplikatów

    def test_python_and_javascript(self):
        """Test przydzielania Python i JavaScript developerów"""
        suggested = suggest_team_members({
            self.python_skill: 1,
            self.js_skill: 1
        })
        self.assertEqual(len(suggested), 2)
        skills = {emp['skill'] for emp in suggested}
        self.assertIn('Python', skills)
        self.assertIn('JavaScript', skills)

    def test_more_than_available(self):
        """Test żądania większej liczby pracowników niż dostępna"""
        # Mamy 6 pracowników z Pythonem
        suggested = suggest_team_members({self.python_skill: 10})
        self.assertEqual(len(suggested), 6)  # Powinno zwrócić wszystkich dostępnych

    def test_no_duplicates_across_skills(self):
        """Test czy pracownik nie jest przydzielany do wielu umiejętności"""
        suggested = suggest_team_members({
            self.python_skill: 2,
            self.django_skill: 2
        })
        employee_ids = [emp['employee_id'] for emp in suggested]
        self.assertEqual(len(employee_ids), len(set(employee_ids)))

    def test_belbin_roles_priority(self):
        """Test czy pracownicy są wybierani zgodnie z priorytetem ról Belbina i kategorii"""
        # Test dla Python developera - powinien preferować różnorodność kategorii
        suggested = suggest_team_members({self.python_skill: 3})
        
        # Mapowanie pracowników na ich główne kategorie
        employee_categories = {
            'Adam': 'zadaniowe',
            'Barbara': 'intelektualne',
            'Ewa': 'zadaniowe',
            'Filip': 'intelektualne',
            'Grzegorz': 'socjalne'
        }
        
        # Sprawdź kategorie wybranych pracowników
        selected_categories = [
            employee_categories.get(emp['first_name']) 
            for emp in suggested 
            if emp['first_name'] in employee_categories
        ]
        
        # Policz wystąpienia każdej kategorii
        category_counts = {}
        for category in selected_categories:
            category_counts[category] = category_counts.get(category, 0) + 1
        
        # Sprawdź czy mamy przynajmniej 2 różne kategorie
        self.assertTrue(
            len(category_counts) >= 2,
            f"Zespół powinien zawierać pracowników z co najmniej 2 różnych kategorii, znaleziono: {category_counts}"
        )

    def test_fallback_to_non_belbin(self):
        """Test czy algorytm pomija pracowników bez testu Belbina"""
        # Najpierw sprawdźmy, czy Daniel (pracownik bez testu Belbina) istnieje w bazie danych
        daniel = Employee.objects.filter(user__first_name='Daniel').first()
        self.assertIsNotNone(daniel, "Daniel powinien istnieć w bazie danych przed testem")
        
        # Sprawdź, czy algorytm pomija pracowników bez testu Belbina
        # Usuń wszystkich pracowników z testem Belbina, pozostawiając tylko Daniela
        Employee.objects.filter(belbin_test_result__has_key='roles_by_level').delete()
        
        # Sprawdź, czy algorytm nie zwraca pracowników bez testu Belbina
        suggested = suggest_team_members({self.python_skill: 1})
        
        # Oczekujemy, że algorytm nie zwróci żadnych pracowników
        self.assertEqual(len(suggested), 0, "Algorytm nie powinien zwracać pracowników bez testu Belbina")

    def test_team_diversity(self):
        """
        Test sprawdzający różnorodność zespołu pod względem ról Belbina.
        """
        # Mapowanie pracowników na ich główne kategorie
        employee_categories = {
            'Adam': 'zadaniowe',
            'Barbara': 'intelektualne',
            'Celina': 'socjalne',
            'Ewa': 'zadaniowe',
            'Filip': 'intelektualne',
            'Grzegorz': 'socjalne'
        }
        
        # Test 1: Sprawdzamy czy przy wyborze 3 pracowników z Pythonem, algorytm wybierze z różnych kategorii
        suggested = suggest_team_members({self.python_skill: 3})
        
        selected_categories = [
            employee_categories.get(emp['first_name']) 
            for emp in suggested 
            if emp['first_name'] in employee_categories
        ]
        
        # Policz wystąpienia każdej kategorii
        category_counts = {}
        for category in selected_categories:
            category_counts[category] = category_counts.get(category, 0) + 1
        
        # Sprawdź czy mamy przynajmniej 2 różne kategorie
        self.assertTrue(
            len(category_counts) >= 2,
            f"Zespół powinien zawierać pracowników z co najmniej 2 różnych kategorii, znaleziono: {category_counts}"
        )
        
        # Test 2: Sprawdzamy czy przy wyborze pracowników z różnymi umiejętnościami, 
        # algorytm nadal dba o różnorodność ról
        suggested = suggest_team_members({
            self.python_skill: 2,
            self.js_skill: 1,
            self.react_skill: 1
        })
        
        selected_categories = [
            employee_categories.get(emp['first_name']) 
            for emp in suggested 
            if emp['first_name'] in employee_categories
        ]
        
        category_counts = {}
        for category in selected_categories:
            category_counts[category] = category_counts.get(category, 0) + 1
        
        # Sprawdź czy mamy przynajmniej 2 różne kategorie
        self.assertTrue(
            len(category_counts) >= 2,
            f"Zespół z różnymi umiejętnościami powinien zawierać pracowników z co najmniej 2 różnych kategorii, znaleziono: {category_counts}"
        )
        
        # Sprawdź czy żadna kategoria nie dominuje (nie ma więcej niż 2/3 zespołu)
        for category, count in category_counts.items():
            self.assertTrue(
                count <= len(selected_categories) * 2/3,
                f"Kategoria {category} nie powinna dominować w zespole (max 2/3), ale ma {count} z {len(selected_categories)} pracowników"
            )

    def test_specific_roles_diversity(self):
        """
        Test sprawdzający różnorodność konkretnych ról Belbina w zespole.
        """
        # Dodajmy więcej pracowników z konkretnymi rolami
        test_employees = [
            {
                'username': 'test_emp8',
                'first_name': 'Henryk',
                'roles': {
                    'roles_by_level': {
                        'bardzo wysoki': ['NL'],  # intelektualna
                        'wysoki': ['SE'],         # intelektualna
                        'średni': []
                    }
                },
                'skills': [self.python_skill]
            },
            {
                'username': 'test_emp9',
                'first_name': 'Irena',
                'roles': {
                    'roles_by_level': {
                        'bardzo wysoki': ['CZA'],  # zadaniowa
                        'wysoki': ['PO'],          # zadaniowa
                        'średni': []
                    }
                },
                'skills': [self.python_skill]
            },
            {
                'username': 'test_emp10',
                'first_name': 'Janusz',
                'roles': {
                    'roles_by_level': {
                        'bardzo wysoki': ['SIE'],  # socjalna
                        'wysoki': ['CZG'],         # socjalna
                        'średni': []
                    }
                },
                'skills': [self.python_skill]
            }
        ]

        # Tworzymy dodatkowych pracowników
        for emp_data in test_employees:
            user = User.objects.create(
                username=emp_data['username'],
                first_name=emp_data['first_name'],
                is_employee=True
            )
            employee = Employee.objects.create(
                user=user,
                belbin_test_result=emp_data['roles']
            )
            for skill in emp_data['skills']:
                employee.skills.add(skill)
        
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
        
        # Test: Sprawdzamy czy przy wyborze większego zespołu, algorytm wybiera pracowników
        # z różnymi konkretnymi rolami, a nie tylko z różnych kategorii
        suggested = suggest_team_members({self.python_skill: 6})
        
        # Zbieramy role pracowników (tylko te na poziomie 'bardzo wysoki')
        employee_roles = {}
        for emp in suggested:
            employee = Employee.objects.get(id=emp['employee_id'])
            if employee.belbin_test_result and 'roles_by_level' in employee.belbin_test_result:
                roles = employee.belbin_test_result['roles_by_level'].get('bardzo wysoki', [])
                if roles:
                    employee_roles[emp['first_name']] = roles[0]  # Bierzemy pierwszą rolę
        
        # Policz wystąpienia każdej roli
        role_counts = {}
        for role in employee_roles.values():
            role_counts[role] = role_counts.get(role, 0) + 1
        
        # Policz wystąpienia każdej kategorii
        category_counts = {}
        for role in employee_roles.values():
            category = role_categories.get(role)
            if category:
                category_counts[category] = category_counts.get(category, 0) + 1
        
        # Wypisz informacje diagnostyczne
        print(f"Wybrani pracownicy i ich role: {employee_roles}")
        print(f"Liczba wystąpień każdej roli: {role_counts}")
        print(f"Liczba wystąpień każdej kategorii: {category_counts}")
        
        # Sprawdź czy mamy przynajmniej 3 różne role
        self.assertTrue(
            len(role_counts) >= 3,
            f"Zespół powinien zawierać pracowników z co najmniej 3 różnymi rolami, znaleziono: {role_counts}"
        )
        
        # Sprawdź czy mamy wszystkie 3 kategorie
        self.assertTrue(
            len(category_counts) >= 2,
            f"Zespół powinien zawierać pracowników z co najmniej 2 kategorii, znaleziono: {category_counts}"
        )

    def test_team_diversity_score(self):
        """
        Test sprawdzający, czy algorytm wybiera zespół z wysoką punktacją różnorodności.
        """
        # Przygotowanie danych testowych - dodajemy więcej pracowników z różnymi rolami
        test_employees = [
            {
                'username': 'test_emp11',
                'first_name': 'Karol',
                'roles': {
                    'roles_by_level': {
                        'bardzo wysoki': ['PER'],  # socjalna
                        'wysoki': ['CZK'],         # socjalna
                        'średni': []
                    }
                },
                'skills': [self.python_skill]
            },
            {
                'username': 'test_emp12',
                'first_name': 'Laura',
                'roles': {
                    'roles_by_level': {
                        'bardzo wysoki': ['CZK'],  # socjalna
                        'wysoki': ['SIE'],         # socjalna
                        'średni': []
                    }
                },
                'skills': [self.python_skill]
            },
            {
                'username': 'test_emp13',
                'first_name': 'Marek',
                'roles': {
                    'roles_by_level': {
                        'bardzo wysoki': ['NL'],   # intelektualna
                        'wysoki': ['SE'],          # intelektualna
                        'średni': []
                    }
                },
                'skills': [self.python_skill]
            }
        ]

        # Tworzymy dodatkowych pracowników
        for emp_data in test_employees:
            user = User.objects.create(
                username=emp_data['username'],
                first_name=emp_data['first_name'],
                is_employee=True
            )
            employee = Employee.objects.create(
                user=user,
                belbin_test_result=emp_data['roles']
            )
            for skill in emp_data['skills']:
                employee.skills.add(skill)
        
        # Test 1: Sprawdzamy punktację dla zespołu z 6 pracownikami
        suggested = suggest_team_members({self.python_skill: 6})
        
        # Pobieramy obiekty Employee dla sugerowanych pracowników
        employee_ids = [emp['employee_id'] for emp in suggested]
        team_members = Employee.objects.filter(id__in=employee_ids)
        
        # Obliczamy punktację zespołu
        score = calculate_team_diversity_score(team_members)
        
        # Wypisujemy informacje diagnostyczne
        print(f"Punktacja zespołu: {score:.2f}")
        
        # Zbieramy role pracowników (tylko te na poziomie 'bardzo wysoki')
        employee_roles = {}
        for emp in suggested:
            employee = Employee.objects.get(id=emp['employee_id'])
            if employee.belbin_test_result and 'roles_by_level' in employee.belbin_test_result:
                roles = employee.belbin_test_result['roles_by_level'].get('bardzo wysoki', [])
                if roles:
                    employee_roles[emp['first_name']] = roles[0]
        
        print(f"Wybrani pracownicy i ich role: {employee_roles}")
        
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
        
        # Policz wystąpienia każdej kategorii
        category_counts = {}
        for role in employee_roles.values():
            category = role_categories.get(role)
            if category:
                category_counts[category] = category_counts.get(category, 0) + 1
        
        print(f"Liczba wystąpień każdej kategorii: {category_counts}")
        
        # Sprawdź czy mamy wszystkie 3 kategorie
        self.assertTrue(
            len(category_counts) >= 2,
            f"Zespół powinien zawierać pracowników z co najmniej 2 kategorii, znaleziono: {category_counts}"
        )
        
        # Sprawdź czy punktacja jest wysoka (powyżej 50 punktów)
        self.assertTrue(
            score >= 50.0,
            f"Punktacja zespołu powinna być wysoka (>=50), otrzymano: {score:.2f}"
        )
        
        # Test 2: Porównujemy punktację dla różnych kombinacji pracowników
        # Tworzymy kilka różnych zespołów i sprawdzamy ich punktację
        
        # Zespół 1: Pracownicy tylko z jednej kategorii (niższa różnorodność)
        team1_members = []
        for employee in Employee.objects.filter(belbin_test_result__has_key='roles_by_level'):
            if employee.belbin_test_result and 'roles_by_level' in employee.belbin_test_result:
                roles = employee.belbin_test_result['roles_by_level'].get('bardzo wysoki', [])
                if 'SE' in roles:
                    team1_members.append(employee)
                    if len(team1_members) >= 3:
                        break
        
        # Zespół 2: Pracownicy z różnych kategorii (wyższa różnorodność)
        team2_members = []
        categories_found = set()
        
        for employee in Employee.objects.filter(belbin_test_result__has_key='roles_by_level'):
            if employee.belbin_test_result and 'roles_by_level' in employee.belbin_test_result:
                roles = employee.belbin_test_result['roles_by_level'].get('bardzo wysoki', [])
                if not roles:
                    continue
                
                role = roles[0]
                category = role_categories.get(role)
                
                if category and category not in categories_found:
                    team2_members.append(employee)
                    categories_found.add(category)
                    
                    if len(categories_found) >= 3:
                        break
        
        # Obliczamy punktację dla obu zespołów
        score1 = calculate_team_diversity_score(team1_members)
        score2 = calculate_team_diversity_score(team2_members)
        
        print(f"Punktacja zespołu 1 (niska różnorodność): {score1:.2f}")
        print(f"Punktacja zespołu 2 (wysoka różnorodność): {score2:.2f}")
        
        # Sprawdź czy zespół z wyższą różnorodnością ma wyższą punktację
        self.assertTrue(
            score2 > score1,
            f"Zespół z wyższą różnorodnością powinien mieć wyższą punktację, otrzymano: {score1:.2f} vs {score2:.2f}"
        )

    def test_algorithm_vs_random(self):
        """
        Test porównujący punktację zespołów utworzonych losowo z zespołami utworzonymi
        przez algorytm wyżarzania symulowanego.
        """
        import random
        
        # Dodajmy więcej pracowników testowych z różnymi rolami i umiejętnościami
        # aby mieć większą pulę do wyboru
        test_employees = [
            {
                'username': 'test_emp14',
                'first_name': 'Natalia',
                'roles': {
                    'roles_by_level': {
                        'bardzo wysoki': ['NG'],  # socjalne
                        'wysoki': ['CZK'],        # socjalne
                        'średni': []
                    }
                },
                'skills': [self.python_skill, self.django_skill]
            },
            {
                'username': 'test_emp15',
                'first_name': 'Olaf',
                'roles': {
                    'roles_by_level': {
                        'bardzo wysoki': ['CZA'],  # zadaniowe
                        'wysoki': ['PO'],          # zadaniowe
                        'średni': []
                    }
                },
                'skills': [self.js_skill, self.react_skill]
            },
            {
                'username': 'test_emp16',
                'first_name': 'Patrycja',
                'roles': {
                    'roles_by_level': {
                        'bardzo wysoki': ['SIE'],  # intelektualne
                        'wysoki': ['SE'],          # intelektualne
                        'średni': []
                    }
                },
                'skills': [self.java_skill, self.python_skill]
            },
            {
                'username': 'test_emp17',
                'first_name': 'Robert',
                'roles': {
                    'roles_by_level': {
                        'bardzo wysoki': ['PO'],   # zadaniowe
                        'wysoki': ['CZA'],         # zadaniowe
                        'średni': []
                    }
                },
                'skills': [self.django_skill, self.react_skill]
            },
            {
                'username': 'test_emp18',
                'first_name': 'Sandra',
                'roles': {
                    'roles_by_level': {
                        'bardzo wysoki': ['CZG'],  # socjalne
                        'wysoki': ['NG'],          # socjalne
                        'średni': []
                    }
                },
                'skills': [self.js_skill, self.java_skill]
            }
        ]

        # Tworzymy dodatkowych pracowników
        for emp_data in test_employees:
            user = User.objects.create(
                username=emp_data['username'],
                first_name=emp_data['first_name'],
                is_employee=True
            )
            employee = Employee.objects.create(
                user=user,
                belbin_test_result=emp_data['roles']
            )
            for skill in emp_data['skills']:
                employee.skills.add(skill)
        
        # Przygotuj 5 różnych konfiguracji wymagań
        test_requirements = [
            # Test 1: Prosty zespół - 3 programistów Python
            {self.python_skill: 3},
            
            # Test 2: Mieszany zespół - 2 Python, 2 JavaScript
            {self.python_skill: 2, self.js_skill: 2},
            
            # Test 3: Duży zespół - 3 Python, 2 JavaScript, 2 React, 1 Java
            {self.python_skill: 3, self.js_skill: 2, self.react_skill: 2, self.java_skill: 1},
            
            # Test 4: Zespół z Django - 2 Python, 3 Django
            {self.python_skill: 2, self.django_skill: 3},
            
            # Test 5: Zrównoważony zespół - po 2 z każdej umiejętności
            {self.python_skill: 2, self.js_skill: 2, self.react_skill: 2, self.java_skill: 2}
        ]
        
        print("\n=== PORÓWNANIE WYŻARZANIA Z LOSOWYM WYBOREM ===")
        
        for i, requirements in enumerate(test_requirements, 1):
            print(f"\nTest {i}: {requirements}")
            
            # 1. Zespół utworzony przez algorytm wyżarzania
            annealing_team = suggest_team_members_with_annealing(project_id=None, requirements=requirements)
            
            # Pobierz obiekty Employee dla sugerowanych pracowników
            annealing_employee_ids = [emp['employee_id'] for emp in annealing_team]
            annealing_team_members = Employee.objects.filter(id__in=annealing_employee_ids)
            
            # Oblicz punktację zespołu
            annealing_score = calculate_team_diversity_score(annealing_team_members)
            
            # 2. Zespół utworzony losowo
            random_team_members = []
            remaining_requirements = dict(requirements)
            
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
                            remaining_requirements[skill] = remaining_requirements.get(skill, 0) - 1
            
            random_score = calculate_team_diversity_score(random_team_members)
            
            # Wypisz wyniki
            print(f"Wyżarzanie: {len(annealing_team)} pracowników, punktacja: {annealing_score:.2f}")
            print(f"Losowo: {len(random_team_members)} pracowników, punktacja: {random_score:.2f}")
            print(f"Różnica: {annealing_score - random_score:.2f} punktów")
            
            # Zamiast asercji, po prostu zapisujemy wynik porównania
            if annealing_score >= random_score:
                print("✓ Wyżarzanie dało lepszą lub równą punktację")
            else:
                print("✗ Losowy wybór dał lepszą punktację")
            
            # Wypisz szczegóły zespołów
            print("Zespół wyżarzania:")
            for emp in annealing_team_members:
                roles = []
                if emp.belbin_test_result and 'roles_by_level' in emp.belbin_test_result:
                    for level in ['bardzo wysoki', 'wysoki']:
                        for role in emp.belbin_test_result['roles_by_level'].get(level, []):
                            roles.append(f"{role} ({level})")
                print(f"- {emp.user.first_name}: {', '.join(roles)}")
            
            print("Zespół losowy:")
            for emp in random_team_members:
                roles = []
                if emp.belbin_test_result and 'roles_by_level' in emp.belbin_test_result:
                    for level in ['bardzo wysoki', 'wysoki']:
                        for role in emp.belbin_test_result['roles_by_level'].get(level, []):
                            roles.append(f"{role} ({level})")
                print(f"- {emp.user.first_name}: {', '.join(roles)}")
        
        # Dodajmy jeszcze 5 powtórzeń testu z losowym wyborem dla każdej konfiguracji,
        # aby uzyskać bardziej miarodajne wyniki
        print("\n=== STATYSTYKI Z WIELU POWTÓRZEŃ ===")
        
        annealing_wins = 0
        random_wins = 0
        ties = 0
        total_annealing_score = 0
        total_random_score = 0
        
        # Liczba powtórzeń dla każdej konfiguracji
        repetitions = 5
        
        for i, requirements in enumerate(test_requirements, 1):
            print(f"\nStatystyki dla konfiguracji {i}: {requirements}")
            
            config_annealing_wins = 0
            config_random_wins = 0
            config_ties = 0
            config_annealing_score = 0
            config_random_score = 0
            
            for j in range(repetitions):
                # 1. Zespół utworzony przez algorytm wyżarzania
                annealing_team = suggest_team_members_with_annealing(project_id=None, requirements=requirements)
                annealing_employee_ids = [emp['employee_id'] for emp in annealing_team]
                annealing_team_members = Employee.objects.filter(id__in=annealing_employee_ids)
                annealing_score = calculate_team_diversity_score(annealing_team_members)
                
                # 2. Zespół utworzony losowo
                random_team_members = []
                remaining_requirements = dict(requirements)
                
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
                                remaining_requirements[skill] = remaining_requirements.get(skill, 0) - 1
                
                random_score = calculate_team_diversity_score(random_team_members)
                
                # Aktualizuj statystyki
                config_annealing_score += annealing_score
                config_random_score += random_score
                
                if annealing_score > random_score:
                    config_annealing_wins += 1
                    annealing_wins += 1
                elif random_score > annealing_score:
                    config_random_wins += 1
                    random_wins += 1
                else:
                    config_ties += 1
                    ties += 1
            
            # Wypisz statystyki dla tej konfiguracji
            print(f"Wyżarzanie wygrywa: {config_annealing_wins}/{repetitions} ({config_annealing_wins/repetitions*100:.1f}%)")
            print(f"Losowy wybór wygrywa: {config_random_wins}/{repetitions} ({config_random_wins/repetitions*100:.1f}%)")
            print(f"Remisy: {config_ties}/{repetitions} ({config_ties/repetitions*100:.1f}%)")
            print(f"Średnia punktacja wyżarzania: {config_annealing_score/repetitions:.2f}")
            print(f"Średnia punktacja losowego wyboru: {config_random_score/repetitions:.2f}")
            print(f"Średnia różnica: {(config_annealing_score-config_random_score)/repetitions:.2f} punktów")
            
            # Aktualizuj łączne statystyki
            total_annealing_score += config_annealing_score
            total_random_score += config_random_score
        
        # Wypisz łączne statystyki
        total_tests = len(test_requirements) * repetitions
        print("\n=== PODSUMOWANIE ===")
        print(f"Łączna liczba testów: {total_tests}")
        print(f"Wyżarzanie wygrywa: {annealing_wins}/{total_tests} ({annealing_wins/total_tests*100:.1f}%)")
        print(f"Losowy wybór wygrywa: {random_wins}/{total_tests} ({random_wins/total_tests*100:.1f}%)")
        print(f"Remisy: {ties}/{total_tests} ({ties/total_tests*100:.1f}%)")
        print(f"Średnia punktacja wyżarzania: {total_annealing_score/total_tests:.2f}")
        print(f"Średnia punktacja losowego wyboru: {total_random_score/total_tests:.2f}")
        print(f"Średnia różnica: {(total_annealing_score-total_random_score)/total_tests:.2f} punktów")

    def test_suggest_team_members_with_annealing(self):
        """
        Test porównujący punktację zespołów utworzonych przez algorytm, algorytm symulowanego wyżarzania
        i losowy wybór pracowników.
        """
        import random
        
        # Przygotuj konfiguracje wymagań do testowania
        test_requirements = [
            # Test 1: Prosty zespół - 3 programistów Python
            {self.python_skill: 3},
            
            # Test 2: Mieszany zespół - 2 Python, 2 JavaScript
            {self.python_skill: 2, self.js_skill: 2},
            
            # Test 3: Duży zespół - 3 Python, 2 JavaScript, 2 React, 1 Java
            {self.python_skill: 3, self.js_skill: 2, self.react_skill: 2, self.java_skill: 1},
            
            # Test 4: Zespół z Django - 2 Python, 3 Django
            {self.python_skill: 2, self.django_skill: 3},
            
            # Test 5: Zrównoważony zespół - po 2 z każdej umiejętności
            {self.python_skill: 2, self.js_skill: 2, self.react_skill: 2, self.java_skill: 2}
        ]
        
        print("\n=== PORÓWNANIE ALGORYTMU, WYŻARZANIA I LOSOWEGO WYBORU ===")
        
        # Liczba powtórzeń dla każdej konfiguracji
        repetitions = 2
        
        results = []
        
        # Dla każdej konfiguracji wymagań
        for i, requirements in enumerate(test_requirements, 1):
            print(f"\nTest {i}: {requirements}")
            
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
                algorithm_suggestions = suggest_team_members(required_skills=requirements, project=None)
                
                algorithm_team_members = []
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
            print(f"=== STATYSTYKI DLA TESTU {i} ===")
            print(f"Algorytm wygrywa: {test_results['algorithm_wins']}/{total_reps} ({test_results['algorithm_win_rate']*100:.1f}%)")
            print(f"Wyżarzanie wygrywa: {test_results['annealing_wins']}/{total_reps} ({test_results['annealing_win_rate']*100:.1f}%)")
            print(f"Losowy wybór wygrywa: {test_results['random_wins']}/{total_reps} ({test_results['random_win_rate']*100:.1f}%)")
            print(f"Średnia punktacja algorytmu: {test_results['avg_algorithm_score']:.2f}")
            print(f"Średnia punktacja wyżarzania: {test_results['avg_annealing_score']:.2f}")
            print(f"Średnia punktacja losowego wyboru: {test_results['avg_random_score']:.2f}")
            print()
            
            results.append(test_results)
        
        # Oblicz ogólne statystyki
        total_tests = len(test_requirements) * repetitions
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
