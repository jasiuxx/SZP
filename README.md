![System_zarzadzania_pracownikami (2)](https://github.com/user-attachments/assets/990c040b-f303-4a6f-9d74-4d59671215dc)


## **Opis projektu**
System zarządzania pracownikami, pracodawcami i projektami oparty na frameworku Django. Głównym celem aplikacji jest automatyzacja procesu tworzenia zespołów projektowych na podstawie kompetencji twardych (umiejętności techniczne) oraz miękkich (cechy osobowościowe, test Belbina). System wspiera pracowników, pracodawców oraz zarządzanie projektami.
## **Jak to działa?**
System opiera się na kwestionariuszu osobowości bazującym na teście Belbina. Test ten na podstawie pytań o różne sytuacje i odczucia w nich sugeruje jaką rolę będzie przyjmował członek zespołu w pracy grupowej. Założeniem mojego systemu jest stworzenie zróżnicowanego zespołu z jak największą ilością niepowtarzających się ról zespołowych. Schemat użycia: Pracownik uzupełnia kwestionariusz na swoim profilu, następnie dodaje informacje o swoich umiejętnościach technicznych, ich stopniu zaawansowania, ewentualnie dołącza swoje doświadczenie. Pracodawca tworząc projekt ustala wymagane kompetencje oraz ilość potrzebnych fachowców. System na podstawie algorytmu wielokryterialnego symulowanego wyżarzania dobiera optymalny zespół, który jest najbardziej różnorodny oraz posiada najwyższy stopień zaawansowania umiejętności. Po utworzeniu pracodawca ma możliwość edytowania projektu oraz zajrzenia na profile wpisanych członków. Pracownicy mają możliwość zobaczyc na swoim profilu w jakich projektach są zapisani oraz mogą wysłać wiadomosc w zespole projektowym.

---

## **Zastosowanie**
- **Pracodawcy**:
  - Automatyczne tworzenie idealnych zespołów projektowych za pomocą jednego kliknięcia.
  - Edycja i usuwanie projektów.
  - Przeglądanie profili pracowników oraz ich umiejętności i doświadczeń.
- **Pracownicy**:
  - Wypełnianie kwestionariusza Belbina w celu lepszego dopasowania do zespołów.
  - Przegląd przypisanych projektów.
  - Dodawanie i edycja swoich umiejętności oraz doświadczeń zawodowych.
  - Łatwy kontakt z członkami zespołu za pomocą systemu wiadomości.

---

## **Funkcjonalności**

### **Moduł pracowników**
- Zarządzanie umiejętnościami technicznymi (`Skill`) oraz poziomem zaawansowania (`EmployeeSkill`).
 ![image](https://github.com/user-attachments/assets/cd07a6e3-8ecb-4cdb-b9e2-b8d9ba9ecbc4)
- Wykonanie kwestionariusza ról zespołowych.
 ![image](https://github.com/user-attachments/assets/5f4151d2-b3a2-46b2-b173-a3a7ac51a67f)
- Przechowywanie wyników testu Belbina w formacie JSON (`belbin_test_result`) oraz szczegółowych punktacji (`BelbinScore`).
 ![image](https://github.com/user-attachments/assets/3f23cc5c-566e-4be5-8e36-af8a9e56394c)
- Dodawanie, edycja i usuwanie doświadczeń zawodowych (`Experience`).
![image](https://github.com/user-attachments/assets/a4dd521f-a41e-45ea-84ca-16fc5aa80284)


### **Moduł pracodawców**
- Rejestracja pracodawców z weryfikacją kodem (`VerificationCode`).
  ![image](https://github.com/user-attachments/assets/7702e855-e808-473d-99c4-ed4fc50da89d)

- Zarządzanie projektami, przypisanymi zespołami i wymaganiami umiejętności.
  ![image](https://github.com/user-attachments/assets/5d1ff2be-43c0-4669-8bd2-c3a97c181d61)


### **Moduł projektów**
- Tworzenie projektów z określonymi wymaganiami umiejętności (`ProjectSkillRequirement`).
![image](https://github.com/user-attachments/assets/803459ff-d13a-4d8f-a11b-127cae6caf40)
- Automatyczne przypisywanie pracowników do projektów na podstawie algorytmu symulowanego wyżarzania.
  ![image](https://github.com/user-attachments/assets/1130ab87-3882-4e48-97f8-e94fa854359d)
- Wyświetlanie szczegółów projektu, zarządzanie wiadomościami oraz edycja zespołów.

### **Test Belbina**
- Realizacja testu osobowościowego z podziałem na kategorie ról (zadaniowe, intelektualne, socjalne).
- Zapis wyników w modelu `Employee` oraz szczegółowych punktacji w `BelbinScore`.

---

## **Zasady działania**

1. **Automatyczne tworzenie zespołów**:
   - Algorytm symulowanego wyżarzania optymalizuje dobór zespołu pod kątem różnorodności ról Belbina i poziomu umiejętności technicznych.
     ![image](https://github.com/user-attachments/assets/12b6dd87-1b36-473f-b2e1-0b2b870c85df)
      ![image](https://github.com/user-attachments/assets/2319160d-c98c-48af-8292-986d34b4230c)
   - Dynamiczne generowanie sąsiednich rozwiązań zapewnia maksymalną efektywność.

2. **Scoring zespołów**:
   - Obliczanie punktacji zespołu na podstawie różnorodności ról Belbina i zaawansowania umiejętnośći technicznych.
     ![image](https://github.com/user-attachments/assets/4fffafc1-2497-4ded-96b4-c139e6a206fe)



3. **Interakcje użytkowników**:
   - Pracownicy mogą aktualizować swoje profile, dodawać doświadczenia i wypełniać test Belbina.
   - Pracodawcy mogą zarządzać projektami i przypisywać do nich optymalne zespoły.

---

## **Technologie**
- Framework: Django
- Baza danych: SQLite 
- Frontend: HTML/CSS z użyciem Bootstrap
- Algorytmy: Python 

Jest to na razie prototyp w trakcie rozwijania, więc w systemie mogą znaleźć się błędy.
---

