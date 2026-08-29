import secrets


def public_id(prefix: str) -> str:
    return f"{prefix}-{secrets.token_hex(3).upper()}"
