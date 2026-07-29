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
