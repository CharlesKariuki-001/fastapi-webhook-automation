"""
Webhook signature verification - the same HMAC pattern Stripe, Shopify,
and most real webhook providers use.

This is the piece the original roadmap's webhook demo explicitly left
out ("no authentication/signature verification included in this
demo"). Since you already built and proved this exact pattern in
python-code-rescue Case 5, it's included here from the start instead
of being a gap you'd have to explain away to a client.
"""

import hashlib
import hmac


def verify_signature(raw_body: bytes, signature_header: str | None, secret: str) -> bool:
    if not signature_header or not secret:
        return False
    expected = hmac.new(secret.encode(), raw_body, hashlib.sha256).hexdigest()
    # compare_digest instead of == to avoid leaking timing information
    # about how much of the signature was correct.
    return hmac.compare_digest(expected, signature_header)
