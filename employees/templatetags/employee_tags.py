from django import template
from employees.models import Employee

register = template.Library()

@register.filter
def get_item(dictionary, key):
    """
    Filtr do pobierania wartości ze słownika po kluczu.
    Użycie: {{ dictionary|get_item:key }}
    """
    print(f"DEBUG - get_item: dictionary={dictionary}, key={key}, type(key)={type(key)}")
    
    if dictionary is None:
        print("DEBUG - get_item: dictionary is None")
        return None
    
    if key is None:
        print("DEBUG - get_item: key is None")
        return None
    
    # Konwertuj key na string
    str_key = str(key)
    print(f"DEBUG - get_item: str_key={str_key}")
    
    # Spróbuj pobrać wartość po kluczu string
    if str_key in dictionary:
        value = dictionary[str_key]
        print(f"DEBUG - get_item: value for str_key={value}")
        return value
    
    # Spróbuj pobrać wartość po kluczu int
    try:
        int_key = int(key)
        print(f"DEBUG - get_item: int_key={int_key}")
        if int_key in dictionary:
            value = dictionary[int_key]
            print(f"DEBUG - get_item: value for int_key={value}")
            return value
    except (ValueError, TypeError):
        print(f"DEBUG - get_item: could not convert key to int")
        pass
    
    # Spróbuj pobrać wartość bezpośrednio po kluczu
    if key in dictionary:
        value = dictionary[key]
        print(f"DEBUG - get_item: value for key={value}")
        return value
    
    # Użyj metody get jako ostateczność
    value = dictionary.get(str_key) or dictionary.get(key)
    print(f"DEBUG - get_item: value from get method={value}")
    
    return value 

@register.filter
def get_employee_id(user):
    """Bezpiecznie pobiera ID pracownika dla użytkownika."""
    if hasattr(user, 'employee') and user.employee:
        return user.employee.id
    
    try:
        employee = Employee.objects.get(user=user)
        return employee.id
    except Employee.DoesNotExist:
        return ''
    
    return '' 