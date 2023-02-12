from django import template
import re

register = template.Library()


@register.filter(name='hide_brackets')
def hide_brackets(value):
    return re.sub('[(].+[)]', '', value)


@register.filter(name='get_range')
def get_range(value):
    return range(value)
