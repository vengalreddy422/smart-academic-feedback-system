from django import template

register = template.Library()

@register.filter(name='dict_get')
def dict_get(dictionary, key):
    """Returns the value for a given key from a dictionary."""
    if isinstance(dictionary, dict):
        return dictionary.get(str(key), '')
    # For QueryDict or similar dictionary-like objects
    if hasattr(dictionary, 'get'):
        return dictionary.get(str(key), '')
    return ''

@register.filter(name='is_in_csv')
def is_in_csv(csv_string, item):
    """Checks if an item is in a comma-separated string."""
    if not csv_string:
        return False
    items = [x.strip() for x in str(csv_string).split(',')]
    return str(item).strip() in items
