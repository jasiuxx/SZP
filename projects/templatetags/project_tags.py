from django import template

register = template.Library()

@register.filter
def get_item(dictionary, key):
    if isinstance(dictionary, dict):
        return dictionary.get(key, 0)
    return 0  # Zwróć 0, jeśli dictionary nie jest typu dict

@register.filter
def has_skill(employees, skill_name):
    return any(employee['skill'] == skill_name for employee in employees) 

@register.filter
def default_if_none(value, default):
    if value is None:
        return default
    return value

@register.filter
def skill_color(skill_name):
    """
    Zwraca klasę koloru Bootstrap na podstawie nazwy umiejętności.
    """
    colors = {
        'Python': 'bg-primary',
        'C++': 'bg-danger',
        'Java': 'bg-success',
        'JavaScript': 'bg-warning text-dark',
        'Project Management': 'bg-info text-dark',
        'SQL': 'bg-secondary',
        'Django': 'bg-success',
        'React': 'bg-info',
        'Angular': 'bg-danger',
        'C#': 'bg-purple',
        'PHP': 'bg-indigo',
        'Ruby': 'bg-pink',
        'Go': 'bg-teal',
        'Swift': 'bg-orange text-dark',
    }
    
    return colors.get(skill_name, 'bg-dark') 