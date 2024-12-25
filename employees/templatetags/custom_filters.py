from django import template

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