"""
Response guardrails for detecting character breaks and problematic responses.
"""

DEFAULT_MAX_RESPONSE_LENGTH = 500
DEFAULT_REQUEST_TIMEOUT = 30.0

CHARACTER_BREAK_PHRASES = [
    "as an ai",
    "as a language model",
    "i cannot",
    "i'm not able to",
    "i don't have the ability",
    "i apologize, but",
    "i'm sorry, but i",
    "my purpose is to",
    "ethical guidelines",
    "openai",
    "anthropic",
    "claude",
    "chatgpt",
]


def needs_fallback(response: str, max_length: int = DEFAULT_MAX_RESPONSE_LENGTH) -> bool:
    if len(response) > max_length:
        return True

    response_lower = response.lower()
    for phrase in CHARACTER_BREAK_PHRASES:
        if phrase in response_lower:
            return True

    return False
