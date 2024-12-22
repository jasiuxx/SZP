from django import template

register = template.Library()

@register.filter
def get_field(form, label):
    for field_name, field in form.fields.items():
        if field.label == label:
            return form[field_name]
    return None
