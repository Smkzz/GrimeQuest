from dataclasses import dataclass
import os
from urllib.parse import urlsplit

@dataclass(frozen=True)
class Settings:
    provider_base: str = ""
    provider_model: str = ""
    provider_key: str = ""
    access_code: str = ""
    ticket_secret: str = ""
    app_origin: str = ""
    max_calls_hour: int = 40
    max_calls_day: int = 200
    public_live: bool = False
    allow_local_provider: bool = False

    @property
    def ready(self) -> bool:
        return bool(self.provider_base and self.provider_model and (self.public_live or len(self.access_code) >= 24))

    def validate(self):
        if not 1 <= self.max_calls_hour <= 1000:
            raise ValueError("GQ_MAX_CALLS_HOUR must be 1..1000")
        if not 1 <= self.max_calls_day <= 10000:
            raise ValueError("GQ_MAX_CALLS_DAY must be 1..10000")
        if self.ticket_secret and not 32 <= len(self.ticket_secret) <= 256:
            raise ValueError("GQ_TICKET_SECRET must be 32..256 characters when set")
        if self.public_live and self.max_calls_day > 200:
            raise ValueError("GQ_PUBLIC_LIVE requires GQ_MAX_CALLS_DAY <= 200")
        if self.public_live and len(self.ticket_secret) < 32:
            raise ValueError("GQ_PUBLIC_LIVE requires a persistent GQ_TICKET_SECRET")
        if self.provider_base:
            u = urlsplit(self.provider_base)
            local = u.hostname in {"localhost", "127.0.0.1", "::1"}
            if u.username or u.password or u.query or u.fragment or not u.hostname:
                raise ValueError("Provider URL must be a server-configured base URL without credentials or query")
            if not (u.scheme == "https" or (self.allow_local_provider and local and u.scheme == "http")):
                raise ValueError("HTTPS is required except explicitly enabled loopback providers")
        if self.app_origin:
            u = urlsplit(self.app_origin)
            if u.scheme != "https" or not u.hostname or u.path not in ("", "/") or u.query or u.fragment or u.username:
                raise ValueError("GQ_APP_ORIGIN must be an HTTPS origin")
        return self

    @classmethod
    def from_env(cls):
        return cls(provider_base=os.getenv("GQ_PROVIDER_BASE", ""), provider_model=os.getenv("GQ_PROVIDER_MODEL", ""),
                   provider_key=os.getenv("GQ_PROVIDER_KEY", ""), access_code=os.getenv("GQ_ACCESS_CODE", ""),
                   ticket_secret=os.getenv("GQ_TICKET_SECRET", ""), app_origin=os.getenv("GQ_APP_ORIGIN", "").rstrip("/"),
                   max_calls_hour=int(os.getenv("GQ_MAX_CALLS_HOUR", "40")),
                   max_calls_day=int(os.getenv("GQ_MAX_CALLS_DAY", "200")),
                   public_live=os.getenv("GQ_PUBLIC_LIVE", "0") == "1",
                   allow_local_provider=os.getenv("GQ_ALLOW_LOCAL_PROVIDER", "0") == "1").validate()
