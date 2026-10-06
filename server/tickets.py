"""HMAC-bound workflow receipts. A receipt is not real-world proof."""
import base64
import hashlib
import hmac
import json
import secrets
import time

class InvalidTicket(ValueError):
    pass

class Tickets:
    def __init__(self, secret: bytes | None = None, clock=time.time):
        self.secret = secret or secrets.token_bytes(32)
        self.clock = clock

    def sign(self, purpose: str, payload: dict, ttl: int = 7200) -> str:
        body = {"purpose": purpose, "exp": int(self.clock()) + ttl, "data": payload}
        encoded = base64.urlsafe_b64encode(json.dumps(body, separators=(",", ":"), sort_keys=True).encode()).decode().rstrip("=")
        sig = hmac.new(self.secret, encoded.encode(), hashlib.sha256).hexdigest()
        return encoded + "." + sig

    def read(self, token: str, purpose: str) -> dict:
        try:
            if len(token) > 14000:
                raise ValueError()
            encoded, sig = token.split(".")
            expected = hmac.new(self.secret, encoded.encode(), hashlib.sha256).hexdigest()
            if not hmac.compare_digest(expected, sig):
                raise ValueError()
            data = json.loads(base64.urlsafe_b64decode(encoded + "=" * (-len(encoded) % 4)))
            if data["purpose"] != purpose or data["exp"] <= self.clock() or not isinstance(data["data"], dict):
                raise ValueError()
            return data["data"]
        except (ValueError, KeyError, TypeError, UnicodeError) as exc:
            raise InvalidTicket("Workflow receipt is invalid or expired. Start a new encounter.") from exc
