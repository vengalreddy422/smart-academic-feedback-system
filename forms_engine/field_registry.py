import re

VALIDATION_PATTERNS = {
    'phone': r'^[6-9]\d{9}$',                 # Indian standard 10-digit
    'pan':   r'^[A-Z]{5}[0-9]{4}[A-Z]$',      # Indian PAN format
    'email': r'^[^@\s]+@[^@\s]+\.[^@\s]+$',   # Simple email
    'apaar_id': r'^\d{12}$',                  # 12-digit numeric
    'aadhaar': r'^\d{12}$',                   # 12-digit numeric
    'number': r'^-?\d+$',                     # Integer
    'float': r'^-?\d+(\.\d+)?$',              # Decimal number
}

VALIDATION_MESSAGES = {
    'phone': 'Invalid format for Phone Number. Must be a 10-digit number starting with 6-9.',
    'pan': 'Invalid format for PAN. Must be in the format AAAAA9999A.',
    'email': 'Invalid format for Email Address.',
    'apaar_id': 'Invalid format for APAAR ID. Must be exactly 12 digits.',
    'aadhaar': 'Invalid format for Aadhaar. Must be exactly 12 digits.',
    'number': 'Must be a valid integer.',
    'float': 'Must be a valid decimal number.',
}

FIELD_REGISTRY = {
    'text':     {'widget': 'text',     'needs_options': False, 'validation': None, 'label': 'Text Input'},
    'textarea': {'widget': 'textarea', 'needs_options': False, 'validation': None, 'label': 'Textarea'},
    'number':   {'widget': 'number',   'needs_options': False, 'validation': 'number', 'label': 'Number'},
    'float':    {'widget': 'number',   'needs_options': False, 'validation': 'float', 'step': '0.01', 'label': 'Decimal Number'},
    'email':    {'widget': 'email',    'needs_options': False, 'validation': 'email', 'label': 'Email'},
    'phone':    {'widget': 'tel',      'needs_options': False, 'validation': 'phone', 'label': 'Phone Number'},
    'pan':      {'widget': 'text',     'needs_options': False, 'validation': 'pan', 'text_transform': 'uppercase', 'label': 'PAN Number'},
    'apaar_id': {'widget': 'text',     'needs_options': False, 'validation': 'apaar_id', 'label': 'APAAR ID'},
    'aadhaar':  {'widget': 'text',     'needs_options': False, 'validation': 'aadhaar', 'label': 'Aadhaar Number'},
    'date':     {'widget': 'date',     'needs_options': False, 'validation': None, 'label': 'Date'},
    'radio':    {'widget': 'radio',    'needs_options': True,  'validation': None, 'label': 'Radio Button'},
    'checkbox': {'widget': 'checkbox', 'needs_options': True,  'validation': None, 'label': 'Checkbox'},
    'select':   {'widget': 'select',   'needs_options': True,  'validation': None, 'label': 'Dropdown'},
    'rating':   {'widget': 'rating',   'needs_options': True,  'validation': None, 'label': 'Rating'},
}

def get_field_choices():
    """Return a list of tuples for Django choices from the registry."""
    return [(k, v['label']) for k, v in FIELD_REGISTRY.items()]

def validate_field(field_type, value):
    """
    Validates a value based on its field_type using the registry.
    Returns (is_valid, error_message).
    """
    if field_type not in FIELD_REGISTRY:
        return True, None

    validation_key = FIELD_REGISTRY[field_type].get('validation')
    if not validation_key:
        return True, None

    pattern = VALIDATION_PATTERNS.get(validation_key)
    if not pattern:
        return True, None

    if value == '' or value is None:
        return True, None

    if not re.match(pattern, str(value)):
        return False, VALIDATION_MESSAGES.get(validation_key, 'Invalid format.')
        
    return True, None
