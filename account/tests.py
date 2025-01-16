from django.test import TestCase, Client
from django.urls import reverse
from account.models import CustomUser
from employers.models import Employer, VerificationCode


class EmployerRegistrationTestCase(TestCase):

    def setUp(self):
        # Konfiguracja klienta i podstawowych danych testowych
        self.client = Client()
        self.register_url = reverse('register_employee')  # Zmień na odpowiednią nazwę URL dla rejestracji
        self.verification_code = VerificationCode.objects.create(code="TESTCODE")

    def test_employer_registration_success(self):
        """
        Test poprawnej rejestracji pracodawcy z ważnym kodem weryfikacyjnym.
        """
        data = {
            "username": "testemployer",
            "first_name": "Test",
            "last_name": "Employer",
            "email": "employer@test.com",
            "password1": "strongpassword123",
            "password2": "strongpassword123",
            "is_employer": True,
            "verification_code": self.verification_code.code,
        }
        response = self.client.post(self.register_url, data)

        # Sprawdź przekierowanie po rejestracji
        self.assertEqual(response.status_code, 302)

        # Sprawdź, czy użytkownik został utworzony
        user = CustomUser.objects.get(username="testemployer")
        self.assertTrue(user.is_employer)

        # Sprawdź, czy profil pracodawcy został utworzony
        employer = Employer.objects.get(user=user)
        self.assertIsNotNone(employer)

        # Sprawdź, czy kod weryfikacyjny został oznaczony jako użyty
        self.verification_code.refresh_from_db()
        self.assertTrue(self.verification_code.is_used)
        self.assertEqual(self.verification_code.employer, employer)

    def test_employer_registration_invalid_code(self):
        """
        Test rejestracji pracodawcy z nieprawidłowym kodem weryfikacyjnym.
        """
        data = {
            "username": "testemployer",
            "first_name": "Test",
            "last_name": "Employer",
            "email": "employer@test.com",
            "password1": "strongpassword123",
            "password2": "strongpassword123",
            "is_employer": True,
            "verification_code": "INVALIDCODE",
        }
        response = self.client.post(self.register_url, data)

        # Sprawdź, czy formularz zwraca błąd
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Podany kod weryfikacyjny jest nieprawidłowy lub już został wykorzystany.")

        # Sprawdź, czy użytkownik NIE został utworzony
        user_exists = CustomUser.objects.filter(username="testemployer").exists()
        self.assertFalse(user_exists)

    def test_employee_registration_success(self):
        """
        Test poprawnej rejestracji pracownika (bez kodu weryfikacyjnego).
        """
        data = {
            "username": "testemployee",
            "first_name": "Test",
            "last_name": "Employee",
            "email": "employee@test.com",
            "password1": "strongpassword123",
            "password2": "strongpassword123",
            "is_employer": False,
        }
        response = self.client.post(self.register_url, data)

        # Sprawdź przekierowanie po rejestracji
        self.assertEqual(response.status_code, 302)

        # Sprawdź, czy użytkownik został utworzony jako pracownik
        user = CustomUser.objects.get(username="testemployee")
        self.assertTrue(user.is_employee)

    def test_registration_password_mismatch(self):
        """
        Test rejestracji z niepasującymi hasłami.
        """
        data = {
            "username": "testuser",
            "first_name": "Test",
            "last_name": "User",
            "email": "user@test.com",
            "password1": "strongpassword123",
            "password2": "wrongpassword456",
            "is_employer": False,
        }
        response = self.client.post(self.register_url, data)

        # Sprawdź, czy formularz zwraca błąd
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'The two password fields didn’t match.')

