from typing import Optional, List
import re


def sanitize_input(text: Optional[str], max_length: Optional[int] = None) -> Optional[str]:
    if not text:
        return None

    text = ''.join(char for char in text if ord(char) >= 32 or char in '\n\t\r')

    text = text.strip()
    
    if max_length and len(text) > max_length:
        text = text[:max_length]
    
    return text if text else None


def validate_sql_injection_patterns(text: Optional[str]) -> bool:
    if not text:
        return True
    
    text_lower = text.lower()
    dangerous_patterns = [
        "union select",
        "union all select",
        "'; drop table",
        "'; delete from",
        "'; update ",
        "'; insert into",
        "'; truncate",
        "'; alter table",
        "exec(",
        "execute(",
        "script>",
        "<script",
        "javascript:",
        "onerror=",
        "onload=",
        "onclick=",
        "onmouseover=",
        "vbscript:",
        "data:text/html",
        "<iframe",
        "<object",
        "<embed",
        "eval(",
        "expression(",
        "<!--",
        "-->",
    ]
    
    for pattern in dangerous_patterns:
        if pattern in text_lower:
            return False
    
    # Check for SQL comment patterns
    if re.search(r'--\s|/\*|\*/|#\s', text_lower):
        return False
    
    return True


def validate_and_sanitize_input(
    text: Optional[str], 
    max_length: Optional[int] = None,
    field_name: str = "input"
) -> Optional[str]:
    if not text:
        return None
    
    if not validate_sql_injection_patterns(text):
        raise ValueError(
            f"Invalid characters detected in field '{field_name}'. "
            "Please remove any SQL injection attempts or malicious code."
        )
    
    return sanitize_input(text, max_length)


def sanitize_list_input(items: List[str], max_length: Optional[int] = None) -> List[str]:
    sanitized = []
    for item in items:
        if item and validate_sql_injection_patterns(item):
            sanitized_item = sanitize_input(item, max_length)
            if sanitized_item:
                sanitized.append(sanitized_item)
    return sanitized


def validate_file_name(filename: Optional[str]) -> bool:
    if not filename:
        return False
    
    dangerous_patterns = [
        '..',
        '/',
        '\\',
        '\x00',
        '<',
        '>',
        ':',
        '"',
        '|',
        '?',
        '*',
    ]
    
    for pattern in dangerous_patterns:
        if pattern in filename:
            return False
    
    if len(filename) > 255:
        return False
    
    return True

