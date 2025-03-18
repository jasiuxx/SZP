from django import template
import hashlib
from employees.models import EmployeeSkill

register = template.Library()

@register.filter
def get_item(dictionary, key):
    """Filtr do pobierania elementu ze słownika na podstawie klucza."""
    return dictionary.get(key)

@register.filter
def get_proficiency_level(employee, skill):
    """
    Zwraca poziom zaawansowania pracownika dla danej umiejętności.
    """
    try:
        employee_skill = EmployeeSkill.objects.get(employee=employee, skill=skill)
        if employee_skill.proficiency_level == '1':
            return "Junior"
        elif employee_skill.proficiency_level == '2':
            return "Mid"
        elif employee_skill.proficiency_level == '3':
            return "Senior"
        else:
            return employee_skill.proficiency_level
    except EmployeeSkill.DoesNotExist:
        return ""

@register.filter
def skill_color(skill_name):
    """
    Automatycznie przypisuje kolor na podstawie nazwy umiejętności.
    Używa funkcji skrótu (hash) nazwy umiejętności, aby zapewnić, że ta sama umiejętność
    zawsze otrzyma ten sam kolor, a różne umiejętności otrzymają różne kolory.
    """
    # Rozszerzona lista klas kolorów Bootstrap i niestandardowych
    color_classes = [
        'bg-primary',                # niebieski
        'bg-secondary',              # szary
        'bg-success',                # zielony
        'bg-danger',                 # czerwony
        'bg-warning text-dark',      # żółty
        'bg-info text-dark',         # jasnoniebieski
        'bg-dark',                   # czarny
        'bg-purple',                 # fioletowy
        'bg-indigo',                 # indygo
        'bg-pink',                   # różowy
        'bg-teal',                   # turkusowy
        'bg-orange text-dark',       # pomarańczowy
        'bg-primary text-warning',   # niebieski z żółtym tekstem
        'bg-success text-warning',   # zielony z żółtym tekstem
        'bg-danger text-warning',    # czerwony z żółtym tekstem
        'bg-dark text-warning',      # czarny z żółtym tekstem
        'bg-purple text-warning',    # fioletowy z żółtym tekstem
        'bg-indigo text-warning',    # indygo z żółtym tekstem
        'bg-pink text-warning',      # różowy z żółtym tekstem
        'bg-teal text-warning',      # turkusowy z żółtym tekstem
        'bg-orange text-primary',    # pomarańczowy z niebieskim tekstem
        'bg-primary text-danger',    # niebieski z czerwonym tekstem
        'bg-success text-danger',    # zielony z czerwonym tekstem
        'bg-dark text-danger',       # czarny z czerwonym tekstem
    ]

    if skill_name.lower() == "java":
        return 'bg-warning'
    
    # Bardziej zaawansowany algorytm przydzielania kolorów
    # Używamy kombinacji długości nazwy i funkcji skrótu, aby zwiększyć różnorodność
    hash_object = hashlib.md5(skill_name.encode())
    hash_hex = hash_object.hexdigest()
    
    # Używamy różnych części skrótu dla różnych cech
    hash_int1 = int(hash_hex[:8], 16)
    hash_int2 = int(hash_hex[8:16], 16)
    hash_int3 = int(hash_hex[16:24], 16)
    
    # Łączymy różne cechy nazwy umiejętności
    combined_hash = hash_int1 + hash_int2 * len(skill_name) + hash_int3 * (ord(skill_name[0]) if skill_name else 0)
    
    # Użyj modulo, aby wybrać kolor z listy
    color_index = combined_hash % len(color_classes)
    
    return color_classes[color_index]
