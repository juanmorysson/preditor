from django import template

register = template.Library()


@register.filter('startswith')
def startswith(text, starts):
    starts = str(starts)
    return text.startswith(starts)
