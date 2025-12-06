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
    
    # Normalize curly quotes to straight quotes for consistent detection
    # U+2018 (LEFT SINGLE QUOTATION MARK) -> U+0027 (APOSTROPHE)
    # U+2019 (RIGHT SINGLE QUOTATION MARK) -> U+0027 (APOSTROPHE)
    # U+201C (LEFT DOUBLE QUOTATION MARK) -> U+0022 (QUOTATION MARK)
    # U+201D (RIGHT DOUBLE QUOTATION MARK) -> U+0022 (QUOTATION MARK)
    text = text.replace('\u2018', "'")  # ' -> '
    text = text.replace('\u2019', "'")  # ' -> '
    text = text.replace('\u201C', '"')  # " -> "
    text = text.replace('\u201D', '"')  # " -> "
    
    text_lower = text.lower()
    dangerous_patterns = [
        # UNION SELECT patterns
        "union select",
        "union all select",
        "'union select",
        "' union select",
        "union select null",
        "union select *",
        "union select current_user",
        "union select user",
        "union select database",
        "union select version",
        "union select @@version",
        "union select schema",
        "union select table_name",
        "union select column_name",
        # SQL command injection
        "'; drop table",
        "'; delete from",
        "'; update ",
        "'; insert into",
        "'; truncate",
        "'; alter table",
        "'; create table",
        "'; drop database",
        "'; exec",
        "'; execute",
        # XSS patterns
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
        # SQL injection patterns - OR conditions
        "or '1'='1",
        "or '1'='1'",
        "or 1=1",
        "or 'a'='a",
        "or 'a'='a'",
        "or \"1\"=\"1",
        "or \"1\"=\"1\"",
        "or \"a\"=\"a",
        "or \"a\"=\"a\"",
        "' or '",
        "' or 1=1",
        "' or '1'='1",
        "\" or \"",
        "\" or 1=1",
        "\" or \"1\"=\"1",
        # OR/AND without space (e.g., OR'1'='1, AND'1'='1)
        "or'1'='1",
        "or'1'='1'",
        "and'1'='1",
        "and'1'='1'",
        "'or'1'='1",
        "'or'1'='1'",
        "'and'1'='1",
        "'and'1'='1'",
        # SQL injection patterns - AND conditions
        "and '1'='1",
        "and '1'='1'",
        "and 1=1",
        "and 'a'='a",
        "and 'a'='a'",
        "' and '",
        "' and 1=1",
        "' and '1'='1",
        "\" and \"",
        "\" and 1=1",
        "\" and \"1\"=\"1",
    ]
    
    for pattern in dangerous_patterns:
        if pattern in text_lower:
            return False
    
    if re.search(r'--\s|/\*|\*/|#\s', text_lower):
        return False
    
    sql_injection_patterns = [
        # OR/AND with 1=1 patterns
        r'\bor\s+[\'"]?1[\'"]?\s*=\s*[\'"]?1[\'"]?',
        r'\band\s+[\'"]?1[\'"]?\s*=\s*[\'"]?1[\'"]?',
        r'\bor\s+[\'"]?[a-z][\'"]?\s*=\s*[\'"]?[a-z][\'"]?',
        r'\band\s+[\'"]?[a-z][\'"]?\s*=\s*[\'"]?[a-z][\'"]?',
        r'[\'"]\s*or\s*[\'"]',
        r'[\'"]\s*and\s*[\'"]',
        # UNION SELECT patterns
        r'[\'"]?\s*union\s+select',
        r'union\s+select\s+null',
        r'union\s+select\s+\*',
        r'union\s+select\s+current_user',
        r'union\s+select\s+user\b',
        r'union\s+select\s+database\b',
        r'union\s+select\s+version\b',
        r'union\s+select\s+@@version',
        r'union\s+select\s+table_name',
        r'union\s+select\s+column_name',
    ]
    
    for pattern in sql_injection_patterns:
        if re.search(pattern, text_lower):
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
