from django import template

register = template.Library()

@register.filter
def get_item(dictionary, key):
    return dictionary.get(key, 0)

@register.filter
def has_skill(employees, skill_name):
    return any(employee['skill'] == skill_name for employee in employees) 