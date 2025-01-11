from django.test import TestCase, Client
from django.urls import reverse
from employees.models import Employee
from account.models import CustomUser


class BelbinTestCase(TestCase):
    def setUp(self):
        # Tworzymy użytkownika i przypisanego pracownika
        self.user = CustomUser.objects.create_user(
            username="testuser", password="password123"
        )
        self.employee = Employee.objects.create(user=self.user)

        # Logujemy użytkownika
        self.client = Client()
        self.client.login(username="testuser", password="password123")

        # URL do widoku testu Belbina
        self.belbin_test_url = reverse("belbin_test")

    def test_belbin_po_only(self):
        """
        Testuje przypadek, gdy wszystkie punkty są przypisane tylko do roli PO.
        """
        # Przygotowanie danych wejściowych: 10 punktów dla pytań przypisanych do PO,
        # 0 punktów dla pozostałych pytań.
        data = {}
        for group_idx in range(1, 8):  # Dla każdej sekcji (grupy)
            for question_idx in range(1, 9):  # Dla każdego pytania w sekcji
                field_name = f"group_{group_idx}_question_{question_idx}"
                data[field_name] = 0

        # Przypisujemy 10 punktów tylko do pytań związanych z rolą PO
        data["group_1_question_7"] = 10  # Sekcja 1, pytanie 7 (PO)
        data["group_2_question_1"] = 10  # Sekcja 2, pytanie 1 (PO)
        data["group_3_question_8"] = 10  # Sekcja 3, pytanie 8 (PO)
        data["group_4_question_4"] = 10  # Sekcja 4, pytanie 4 (PO)
        data["group_5_question_2"] = 10  # Sekcja 5, pytanie 2 (PO)
        data["group_6_question_6"] = 10  # Sekcja 6, pytanie 6 (PO)
        data["group_7_question_5"] = 10  # Sekcja 7, pytanie 5 (PO)

        # Wysyłamy dane POST do widoku Belbina
        response = self.client.post(self.belbin_test_url, data)

        # Debugowanie: sprawdź status odpowiedzi HTTP
        print("HTTP Response Status:", response.status_code)

        # Debugowanie: sprawdź dane przesłane przez formularz
        print("Dane przesłane przez formularz:", data)

        # Sprawdzamy przekierowanie po zapisaniu wyników
        self.assertEqual(response.status_code, 302)

        # Pobieramy wyniki z bazy danych
        self.employee.refresh_from_db()

        # Debugowanie: sprawdź wynik zapisany w bazie danych
        print("Wynik zapisany w bazie danych:", self.employee.belbin_test_result)

        # Sprawdzamy wynik testu Belbina
        expected_result = {
            "roles_by_level": {
                "bardzo wysoki": ["PO"],
                "wysoki": [],
                "średni": []
            }
        }
        self.assertEqual(self.employee.belbin_test_result, expected_result)
