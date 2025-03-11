#!/usr/bin/env python
import os
import django

# Konfiguracja Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'SZP.settings')
django.setup()

# Import funkcji testowej
from projects.views import test_suggest_team_members

if __name__ == "__main__":
    print("Uruchamiam testy algorytmu suggest_team_members...")
    test_suggest_team_members()
    print("Testy zakończone.") 