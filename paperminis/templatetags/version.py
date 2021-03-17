from django import template
from paperminis import VERSION

register = template.Library()

@register.simple_tag
def version():
    return VERSION
