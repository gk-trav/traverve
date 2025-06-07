import re
from django import template
from django.utils.safestring import mark_safe

register = template.Library()

@register.filter(name='clean_slug')
def clean_slug(value):
    if not isinstance(value, str):
        return value

    value = value.strip().lower() 
    value = value.replace(' ', '-')
    value = re.sub(r'[^A-Za-z0-9\-]', '', value)       
    value = re.sub(r'\s+-\s*|\s*-\s+', '-', value)      
    value = re.sub(r'-+', '-', value)                   
    return re.sub(r'^-+|-+$', '', value)   

@register.filter(name='clean_nl2br')
def clean_nl2br(value):
    if not isinstance(value, str):
        return value
    # Replace \n\n and \n with <br>
    value = value.replace("\\n\\n", "<br>").replace("\\n", "<br>")
    return mark_safe(value)       

@register.filter
def index(sequence, position):
    try:
        return sequence[position]
    except (IndexError, TypeError):
        return ''     
