from django import template
import hashlib  # Upewnij się, że hashlib jest zaimportowane

register = template.Library()

@register.filter
def get_dynamic_field(data, key):
    """ Pobiera dynamicznie pole z form.data """
    return data.get(key, None)


def endswith(value, suffix):
    """Sprawdza, czy wartość kończy się na określony sufiks."""
    if isinstance(value, str):
        return value.endswith(suffix)
    return False

@register.filter
def get_item(dictionary, key):
    """
    Filtr do dostępu do elementów słownika za pomocą klucza, nawet jeśli klucz zawiera spacje.
    Użycie: {{ dictionary|get_item:"klucz z spacjami" }}
    """
    # Sprawdzenie, czy klucz jest typu str
    if isinstance(key, str):
        return dictionary.get(key, [])
    elif isinstance(key, (int, float)):
        # Jeśli klucz jest liczbą, konwertujemy go na string
        return dictionary.get(str(key), [])
    else:
        # Zwracamy pustą listę, jeśli klucz jest innego typu
        return []

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