from django import template

register = template.Library()


@register.filter
def get_item(dictionary, key):
    """Dict lookup by a template loop variable - Django's dot-lookup can't
    do this since `dict.day` looks up the literal string "day", not the
    value of the `day` loop variable."""
    return dictionary.get(key)
