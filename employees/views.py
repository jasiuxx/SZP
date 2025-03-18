from django.shortcuts import render, redirect, get_object_or_404
from django.views import View
from django.contrib.auth.decorators import login_required
from django.utils.decorators import method_decorator
from employees.models import Employee, BelbinScore, Experience
from .forms import GroupedTableForm, ExperienceForm
from django.contrib import messages
from django.core.exceptions import PermissionDenied


class EmployeeBelbinTest(View):
    template_name = 'employees/belbin_test.html'

    questions = [
        {
            'name': 'Część I: Sądzę, że osobiście wnoszę do grupy...',
            'questions': [
                'Wydaje mi się, że szybko dostrzegam i umiem wykorzystać nowe możliwości ',
                'Mogę dobrze pracować z bardzo różnymi ludźmi',
                '"Produkowanie" pomysłów to moja naturalna zdolność',
                'Moja siła tkwi w tym, że potrafię z ludzi "wyciągnąć" to, co mają w sobie najlepszego, aby przyczynili się do osiągnięcia celów i zadań grupowych',
                'Moja główna umiejętność polega na doprowadzaniu spraw do końca i wiąże się z efektywnością',
                'Jestem w stanie przez jakiś czas zaakceptować niepopularność mojej osoby, jeśli prowadzi to do wartościowych wyników',
                'Zwykle wyczuwam, co jest realistyczne i prawdopodobne, jeśli chodzi o osiągniecie sukcesu',
                'Zwykle mogę zaproponować jakieś alternatywne wyjście bez uprzedzeń i niechęci'
            ]
        },
        {
            'name': 'Część II: Jeśli mam jakieś niedociągnięcia w pracy grupowej to dlatego, że...',
            'questions': [
                'Nie mogę się uspokoić, dopóki narada nie jest uporządkowana, kontrolowana i ogólnie dobrze prowadzona',
                'Mam skłonność do bycia wspaniałomyślnym dla tych, których przekonujące pomysły nie zostały odpowiednio przemyślane',
                'Mam skłonność do gadulstwa, gdy grupa rozpracowuje nowe pomysły',
                'Mój chłodny ogląd spraw utrudnia mi przyłączenie się do gotowości i entuzjazmu kolegów',
                'Czasami jestem spostrzegany jako wywierający nadmierny nacisk i autorytatywny wpływ, jeśli coś musi zostać rzeczywiście zrobione',
                'Trudno mi kierować "na pierwszej linii", gdyż czuję się zbyt odpowiedzialny za atmosferę grupową',
                'Mam skłonność do rozmyślania o tym, co w danej chwili wpada mi do głowy, przez co tracę kontakt z tym, co się dzieje',
                'Koledzy widzą mnie jako niepotrzebnie przejmującego się szczegółami i możliwością, że sprawy mogą się źle ułożyć'
            ]
        },
        {
            'name': 'Część III: Gdy jestem wciągnięty razem z innymi w przygotowanie projektu...',
            'questions': [
                'Mam skłonność do wywierania wpływu na ludzi, lecz bez wywierania na nich presji',
                'Moja czujność pozwala zapobiegać wielu pomyłkom i błędom',
                'Jestem gotów kłaść nacisk na działanie, aby upewnić się, że narada nie jest stratą czasu lub, że prowadzi do utracenia z widoku głównego celu',
                'Zwykle można na mnie polegać, że wymyślę coś oryginalnego',
                'Zawsze jestem gotów uczynić dobrą sugestię przedmiotem zainteresowania całej grupy',
                'Zawsze poszukuję ostatnich nowinek, nowych odkryć i wyników badań na określony temat',
                'Mam przekonanie, że moja umiejętność wydawania sądu może pomóc w podjęciu odpowiednich ',
                'Moją specjalnością jest zorganizowanie najbardziej znaczącej części pracy'
            ]
        },
        {
            'name': 'Część IV: Moją charakterystyczną cechą w pracy grupowej jest...',
            'questions': [
                'Rzeczywiście interesuję się bliższym poznaniem moich kolegów',
                'Nie mam oporów przed przeciwstawianiem się zdaniu większości',
                'Zwykle potrafię przyjąć taką linię argumentacji, aby obalić błędny punkt widzenia',
                'Sądzę, że mam szczególny talent do wprowadzania pomysłów w życie, gdy plan ma być zastosowany',
                'Mam skłonność do unikania tego, co oczywiste i do zaskakiwania czymś niespodziewanym',
                'Doprowadzam to, czego się podejmę do perfekcji',
                'Jestem gotów do nawiązywania i wykorzystywania kontaktów pozagrupowych, jeśli jest to potrzebne',
                'Nawet jeśli interesuje mnie wiele aspektów sprawy, nie mam problemów z podjęciem decyzji co do wyboru rozwiązania'
            ]
        },
        {
            'name': 'Część V: Czerpię satysfakcję z pracy, gdyż...',
            'questions': [
                'Cieszy mnie analizowanie sytuacji i rozważanie możliwości wyboru',
                'Interesuje mnie znalezienie praktycznych rozwiązań problemów',
                'Lubię mieć przekonanie, że sprzyjam kształtowaniu dobrych kontaktów międzyludzkich w pracy',
                'Lubię mieć duży wpływ na decyzje',
                'Cieszę się z kontaktów z ludźmi, którzy mają coś nowego do zaoferowania',
                'Jestem w stanie doprowadzić do zgody w ważnych dla pracy sprawach',
                'Wczuwam się w moją część zadania, jeśli pragnę poświęcić zadaniu całą swoją uwagę ',
                'Lubię znaleźć taki obszar, który pobudza moja wyobraźnię'
            ]
        },
        {
            'name': 'Część VI: Jeśli nagle otrzymuję trudne zadanie do wykonania w ograniczonym czasie i wobec nieznanych mi osób...',
            'questions': [
                'Mam ochotę zaszyć się w kącie, aby wymyślić sposób na wyjście z impasu',
                'Byłbym gotów do współpracy z osobą, która wykazała najbardziej pozytywne nastawienie',
                'Znalazłbym sposób na zmniejszenie skali zadania prze ustalenie, co mogłyby zrobić poszczególne jednostki',
                'Moje naturalne wyczucie spraw pilnych pozwoli na postępowanie zgodnie z planem',
                'Z pewnością zachowam spokój i zdolność do trzeźwego osądu',
                'Mimo nacisków zachowam stałość celu',
                'Byłbym przygotowany do przejęcia konstruktywnego kierownictwa, jeśli stwierdziłbym, że grupa nie robi postępu',
                'Zainicjowałbym dyskusję w celu stymulowania nowych pomysłów, rozwiązań'
            ]
        },
        {
            'name': 'Część VII: W odniesieniu do problemów, za które jestem w grupie odpowiedzialny...',
            'questions': [
                'Mam skłonność do ujawniania niezadowolenia wobec tych, którzy moim zdaniem przeszkadzają w osiąganiu postępów',
                'Inni mogą mnie krytykować za to, że jestem analityczny i niedostatecznie opieram się na intuicji',
                'Moje pragnienie, aby praca została starannie wykonana, może wstrzymywać pójście do przodu',
                'Mam skłonność do nudzenia się i oczekuję, że inni będą mnie stymulować i "zapalać"',
                'Trudno mi rozpocząć, jeśli cele nie są dla mnie  jasne',
                'Czasami nie jestem tak efektywny, jak bym chciał, jeśli chodzi o wyjaśnienie złożonych problemów, jakie przede mną stoją',
                'Mam świadomość, że wymagam od innych rzeczy, których sam nie mogę zrobić',
                'Waham się, gdy należałoby przeforsować mój punkt widzenia, gdy mam do czynienia z jawną opozycją'
            ]
        }
    ]

    answers_sum_mapping = [
        {
            'name': 'PO',
            'mapping': [[1, 7], [2, 1], [3, 8], [4, 4], [5, 2], [6, 6], [7, 5]],
            'sum': 0
        },
        {
            'name': 'NL',
            'mapping': [[1, 4], [2, 2], [3, 1], [4, 8], [5, 6], [6, 3], [7, 7]],
            'sum': 0
        },
        {
            'name': 'CZA',
            'mapping': [[1, 6], [2, 5], [3, 3], [4, 2], [5, 4], [6, 7], [7, 1]],
            'sum': 0
        },
        {
            'name': 'SIE',
            'mapping': [[1, 3], [2, 7], [3, 4], [4, 5], [5, 8], [6, 1], [7, 6]],
            'sum': 0
        },
        {
            'name': 'CZK',
            'mapping': [[1, 1], [2, 3], [3, 6], [4, 7], [5, 5], [6, 8], [7, 4]],
            'sum': 0
        },
        {
            'name': 'SE',
            'mapping': [[1, 8], [2, 4], [3, 7], [4, 3], [5, 1], [6, 5], [7, 2]],
            'sum': 0
        },
        {
            'name': 'CZG',
            'mapping': [[1, 2], [2, 6], [3, 5], [4, 1], [5, 3], [6, 5], [7, 8]],
            'sum': 0
        },
        {
            'name': 'PER',
            'mapping': [[1, 5], [2, 8], [3, 2], [4, 6], [5, 7], [6, 4], [7, 3]],
            'sum': 0
        }
    ]

    score_ranges = {
        'PO': {'średni': (7, 11), 'wysoki': (12, 16), 'bardzo wysoki': (17, float('inf'))},
        'NL': {'średni': (7, 10), 'wysoki': (11, 13), 'bardzo wysoki': (14, float('inf'))},
        'CZA': {'średni': (9, 13), 'wysoki': (14, 17), 'bardzo wysoki': (18, float('inf'))},
        'SIE': {'średni': (5, 8), 'wysoki': (9, 12), 'bardzo wysoki': (13, float('inf'))},
        'CZK': {'średni': (7, 9), 'wysoki': (10, 11), 'bardzo wysoki': (12, float('inf'))},
        'SE': {'średni': (6, 9), 'wysoki': (10, 12), 'bardzo wysoki': (13, float('inf'))},
        'CZG': {'średni': (9, 12), 'wysoki': (13, 16), 'bardzo wysoki': (17, float('inf'))},
        'PER': {'średni': (4, 6), 'wysoki': (7, 9), 'bardzo wysoki': (10, float('inf'))},
    }

    @method_decorator(login_required)
    def get(self, request):
        # Przygotowanie danych początkowych
        initial_data = {}
        for group_idx, group in enumerate(self.questions, start=1):
            for question_idx in range(1, len(group['questions']) + 1):
                field_name = f"group_{group_idx}_question_{question_idx}"
                initial_data[field_name] = 0  # Ustawienie domyślnej wartości na 0

        # Tworzenie formularza z danymi początkowymi
        form = GroupedTableForm(grouped_questions=self.questions, initial=initial_data)
        return render(request, self.template_name, {'form': form})

    @method_decorator(login_required)
    def post(self, request):
        """
        Obsługuje zapis danych z formularza (punktów), oblicza wynik Belbina i zapisuje:
         1. JSON w polu employee.belbin_test_result (mapowanie poziomów),
         2. Szczegółowe punktacje w modelu BelbinScore (osobna tabela).
        """
        form = GroupedTableForm(request.POST, grouped_questions=self.questions)
        if form.is_valid():
            cleaned_data = form.cleaned_data
            fields_with_values = {
                field_name: field_value for field_name, field_value in cleaned_data.items()
            }

            # 1. Oblicz sumy punktów dla każdej roli
            for item in self.answers_sum_mapping:
                role_mapping_list = item['mapping']  # np. [[1,7], [2,1], ...]
                role_sum = 0

                # Zsumuj punkty z formularza dla danej roli
                for group_idx, question_idx in role_mapping_list:
                    field_key = f"group_{group_idx}_question_{question_idx}"
                    role_sum += fields_with_values.get(field_key, 0)

                item['sum'] = role_sum

            # 2. Na podstawie sum przypisz poziomy (średni, wysoki, bardzo wysoki)
            results_by_level = {
                "bardzo wysoki": [],
                "wysoki": [],
                "średni": [],
            }

            for role in self.answers_sum_mapping:
                role_name = role['name']
                score = role['sum']

                # Przypisz poziom na podstawie zakresów
                for level_name in ["bardzo wysoki", "wysoki", "średni"]:
                    range_min = self.score_ranges[role_name][level_name][0]
                    range_max = self.score_ranges[role_name][level_name][1]
                    if range_min <= score <= range_max:
                        results_by_level[level_name].append(role_name)
                        break

            # 3. Zapisz do modelu Employee (JSON w polu belbin_test_result)
            employee = Employee.objects.get(user=request.user)
            employee.belbin_test_result = {
                "roles_by_level": results_by_level
                # Możesz dodać inne klucze, np. "scores" itp.
            }
            employee.save()

            # 4. (Opcjonalnie) skasuj stare wpisy w BelbinScore, by mieć zawsze aktualne
            employee.belbin_scores.all().delete()

            # 5. Utwórz nowe rekordy w tabeli BelbinScore (punktacja szczegółowa)
            for item in self.answers_sum_mapping:
                print(f"[DEBUG] Rola: {item['name']} finalny sum: {item['sum']}")
                role_name = item['name']  # np. 'PO', 'NL', ...
                role_score = item['sum']
                BelbinScore.objects.create(
                    employee=employee,
                    role_name=role_name,
                    score=role_score
                )

            # 6. Przekieruj do wyników testu
            return redirect('belbin_results')

        # Jeśli formularz nie jest poprawny, wyświetl go ponownie z błędami
        return render(request, self.template_name, {'form': form})


@login_required
def belbin_results_view(request):
    try:
        employee = Employee.objects.get(user=request.user)
        results = employee.belbin_test_result

        # Pobieramy wszystkie rekordy z BelbinScore
        scores = employee.belbin_scores.all().order_by('-score')  # np. sortowanie malejąco po punktach
    except Employee.DoesNotExist:
        results = None
        scores = []

    return render(request, 'employees/belbin_results.html', {
        'results': results,
        'scores': scores,
    })


@login_required
def employee_profile(request, employee_id):
    """Widok profilu pracownika - widoczny dla pracodawców i innych pracowników"""
    employee = get_object_or_404(Employee, id=employee_id)
    return render(request, 'employees/employee_profile.html', {'employee': employee})

@login_required
def my_profile(request):
    """Widok własnego profilu pracownika - widoczny tylko dla zalogowanego pracownika"""
    # Upewnij się, że użytkownik jest powiązany z profilem pracownika
    try:
        employee = request.user.employee
    except AttributeError:
        try:
            employee = Employee.objects.get(user=request.user)
            request.user.employee = employee
        except Employee.DoesNotExist:
            messages.error(request, 'Nie znaleziono profilu pracownika.')
            return redirect('profile')
    
    return render(request, 'employees/employee_profile_my.html', {'employee': employee})

@login_required
def add_experience(request):
    # Upewnij się, że użytkownik jest powiązany z profilem pracownika
    try:
        employee = request.user.employee
    except AttributeError:
        try:
            employee = Employee.objects.get(user=request.user)
            request.user.employee = employee
        except Employee.DoesNotExist:
            messages.error(request, 'Nie znaleziono profilu pracownika.')
            return redirect('profile')
            
    if request.method == 'POST':
        form = ExperienceForm(request.POST, request.FILES)
        if form.is_valid():
            experience = form.save(commit=False)
            experience.employee = employee
            experience.save()
            messages.success(request, 'Doświadczenie zostało dodane pomyślnie.')
            return redirect('employee_profile', employee_id=employee.id)
    else:
        form = ExperienceForm()
    
    return render(request, 'employees/experience_form.html', {
        'form': form,
    })

@login_required
def edit_experience(request, experience_id):
    # Upewnij się, że użytkownik jest powiązany z profilem pracownika
    try:
        employee = request.user.employee
    except AttributeError:
        try:
            employee = Employee.objects.get(user=request.user)
            request.user.employee = employee
        except Employee.DoesNotExist:
            messages.error(request, 'Nie znaleziono profilu pracownika.')
            return redirect('profile')
            
    experience = get_object_or_404(Experience, id=experience_id)
    
    # Weryfikacja czy użytkownik ma uprawnienia do edycji
    if experience.employee.id != employee.id:
        raise PermissionDenied("Nie masz uprawnień do edycji tego doświadczenia.")
    
    if request.method == 'POST':
        form = ExperienceForm(request.POST, request.FILES, instance=experience)
        if form.is_valid():
            form.save()
            messages.success(request, 'Doświadczenie zostało zaktualizowane pomyślnie.')
            return redirect('employee_profile', employee_id=employee.id)
    else:
        form = ExperienceForm(instance=experience)
    
    return render(request, 'employees/experience_form.html', {
        'form': form,
        'experience': experience,
    })

@login_required
def delete_experience(request, experience_id):
    # Upewnij się, że użytkownik jest powiązany z profilem pracownika
    try:
        employee = request.user.employee
    except AttributeError:
        try:
            employee = Employee.objects.get(user=request.user)
            request.user.employee = employee
        except Employee.DoesNotExist:
            messages.error(request, 'Nie znaleziono profilu pracownika.')
            return redirect('profile')
            
    experience = get_object_or_404(Experience, id=experience_id)
    
    # Weryfikacja czy użytkownik ma uprawnienia do usunięcia
    if experience.employee.id != employee.id:
        raise PermissionDenied("Nie masz uprawnień do usunięcia tego doświadczenia.")
    
    if request.method == 'POST':
        experience.delete()
        messages.success(request, 'Doświadczenie zostało usunięte pomyślnie.')
        return redirect('employee_profile', employee_id=employee.id)
    
    return render(request, 'employees/delete_experience.html', {
        'experience': experience,
    })

