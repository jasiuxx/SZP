from django import template

register = template.Library()

@register.filter
def add_class(field, css_class):
    """Dodaje klasę CSS do pola formularza."""
    return field.as_widget(attrs={"class": css_class})

@register.filter
def endswith(value, suffix):
    """Sprawdza, czy wartość kończy się na określony sufiks."""
    if isinstance(value, str):
        return value.endswith(suffix)
    return False