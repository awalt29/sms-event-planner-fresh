import re
import phonenumbers
from phonenumbers import geocoder, carrier


def normalize_phone(phone):
    """
    Normalize phone number by removing formatting characters.
    
    Args:
        phone (str): Phone number with potential formatting
        
    Returns:
        str: Normalized phone number with only digits
    """
    if not phone:
        return ""
    
    # Remove all non-digit characters
    normalized = re.sub(r'[^\d]', '', str(phone))
    
    # Handle US numbers - add country code if missing
    if len(normalized) == 10:
        normalized = '1' + normalized
    
    return normalized


def format_phone_display(phone):
    """
    Format phone number for clean display: (123) 456-7890
    
    Args:
        phone (str): Phone number to format
        
    Returns:
        str: Formatted phone number
    """
    if not phone:
        return ""
    
    # First normalize to remove any existing formatting
    clean = normalize_phone(phone)
    
    # Handle different lengths
    if len(clean) == 11 and clean.startswith('1'):
        # US number with country code
        clean = clean[1:]  # Remove country code for display
    elif len(clean) == 10:
        # US number without country code
        pass
    else:
        # International or invalid number - return as-is
        return phone
    
    # Format as (123) 456-7890
    if len(clean) == 10:
        return f"({clean[:3]}) {clean[3:6]}-{clean[6:]}"
    
    return phone


def format_phone_for_twilio(phone):
    """
    Format phone number for Twilio API (+1234567890)
    
    Args:
        phone (str): Phone number to format
        
    Returns:
        str: Phone number formatted for Twilio
    """
    normalized = normalize_phone(phone)
    
    if not normalized:
        return ""
    
    # Ensure US country code
    if len(normalized) == 10:
        normalized = '1' + normalized
    elif len(normalized) == 11 and not normalized.startswith('1'):
        # International number - keep as-is
        pass
    
    return '+' + normalized


def validate_phone_number(phone):
    """
    Validate phone number using phonenumbers library.
    
    Args:
        phone (str): Phone number to validate
        
    Returns:
        dict: Validation result with is_valid, country, carrier info
    """
    try:
        # Parse the number (assume US if no country code)
        parsed = phonenumbers.parse(phone, "US")
        
        is_valid = phonenumbers.is_valid_number(parsed)
        country = geocoder.description_for_number(parsed, "en")
        carrier_name = carrier.name_for_number(parsed, "en")
        
        return {
            'is_valid': is_valid,
            'country': country,
            'carrier': carrier_name,
            'international_format': phonenumbers.format_number(parsed, phonenumbers.PhoneNumberFormat.INTERNATIONAL),
            'national_format': phonenumbers.format_number(parsed, phonenumbers.PhoneNumberFormat.NATIONAL),
            'e164_format': phonenumbers.format_number(parsed, phonenumbers.PhoneNumberFormat.E164)
        }
    except phonenumbers.NumberParseException:
        return {
            'is_valid': False,
            'error': 'Invalid phone number format'
        }


def extract_phone_numbers_from_text(text):
    """
    Extract phone numbers from text using regex patterns.
    
    Args:
        text (str): Text to search for phone numbers
        
    Returns:
        list: List of phone numbers found in text
    """
    if not text:
        return []
    
    # Common phone number patterns
    patterns = [
        r'\b\d{3}-\d{3}-\d{4}\b',  # 123-456-7890
        r'\b\(\d{3}\)\s*\d{3}-\d{4}\b',  # (123) 456-7890
        r'\b\d{3}\.\d{3}\.\d{4}\b',  # 123.456.7890
        r'\b\d{10}\b',  # 1234567890
        r'\b1\s*\d{3}\s*\d{3}\s*\d{4}\b',  # 1 123 456 7890
        r'\+1\s*\d{3}\s*\d{3}\s*\d{4}\b',  # +1 123 456 7890
    ]
    
    found_numbers = []
    for pattern in patterns:
        matches = re.findall(pattern, text)
        found_numbers.extend(matches)
    
    # Normalize and deduplicate
    normalized_numbers = []
    for number in found_numbers:
        normalized = normalize_phone(number)
        if normalized and normalized not in normalized_numbers:
            normalized_numbers.append(normalized)
    
    return normalized_numbers
