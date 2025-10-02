from django import template

register = template.Library()

@register.filter
def pluck(queryset_or_list, key):
    """
    Extract a list of values for the given key from a list of dicts or QuerySet.values().
    Example:
        [{'month': 'Jan', 'count': 5}, {'month': 'Feb', 'count': 10}] | pluck:'month'
        -> ['Jan', 'Feb']
    """
    try:
        return [item.get(key) for item in queryset_or_list]
    except AttributeError:
        return [getattr(item, key, None) for item in queryset_or_list]

@register.filter
def mul(value, arg):
    """
    Multiply value by arg.
    Example: {{ 5|mul:3 }} -> 15
    """
    try:
        return float(value) * float(arg)
    except (ValueError, TypeError):
        return 0
