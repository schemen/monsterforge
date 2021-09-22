from django.template.defaulttags import register
import os


@register.filter
def env(key):
    return os.environ.get(key, None)
