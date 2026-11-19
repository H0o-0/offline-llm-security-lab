"""Output filtering layer: block responses that contain a protected secret
before they leave the agent. Catches plain, spaced-out / punctuated and
base64-encoded forms of each secret."""
import base64, re

BLOCKED = "[blocked: response contained protected data]"
_NOISE = r"[\s\-_.`'\"]"


def find_secret(secret, text):
    """Return how the secret appears in text ("plain" / "base64"), or None."""
    flat = re.sub(_NOISE, "", text).upper()
    core = re.sub(r"[\s\-_]", "", secret).upper()
    if core and core in flat:
        return "plain"
    b64 = base64.b64encode(secret.encode()).decode().rstrip("=")
    if b64 and b64 in text:
        return "base64"
    return None


def filter_output(text, secrets):
    """Return (safe_text, reason). reason is None when nothing was blocked."""
    for s in secrets:
        hit = find_secret(s, text)
        if hit:
            return BLOCKED, hit
    return text, None
