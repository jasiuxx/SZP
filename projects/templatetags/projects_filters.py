from django import template

register = template.Library()

@register.filter
def get_item(dictionary, key):
    """Filtr do pobierania elementu ze słownika na podstawie klucza."""
    return dictionary.get(key)
