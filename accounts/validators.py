# accounts/validators.py

import re
from django.core.exceptions import ValidationError

def validate_tz_phone(value):
    """
    Ensures the phone number matches +255 followed by 9 digits.
    Example valid phone: +255712345678
    """
    pattern = r'^\+255\d{9}$'
    if not re.match(pattern, value):
        raise ValidationError("Phone number must be in the format: +255XXXXXXXXX (9 digits after +255).")
