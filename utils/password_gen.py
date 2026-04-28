import secrets
import string

def generate_password(length: int = 20, use_symbols: bool = True, use_numbers: bool = True) -> str:
    chars = string.ascii_letters

    if use_numbers:
        chars += string.digits
    if use_symbols:
        chars += string.punctuation

    while True:
        password = ''.join(secrets.choice(chars) for _ in range(length))

        has_upper = any(c.isupper() for c in password)
        has_lower = any(c.islower() for c in password)
        has_digit = any(c.isdigit() for c in password) if use_numbers else True
        has_symbol = any(c in string.punctuation for c in password) if use_symbols else True

        if has_upper and has_lower and has_digit and has_symbol:
            return password