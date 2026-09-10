"""Small project-owned authentication boundary for local Trial Ledger use."""

from __future__ import annotations

from typing import Any, Mapping, Protocol


class AuthenticationError(ValueError):
    """Raised when a supplied authentication context has no local principal."""


class Authenticator(Protocol):
    """Resolves an opaque authentication context to one authenticated actor."""

    def authenticate(self, auth_context: Any) -> str:
        """Return the authenticated actor ID or raise AuthenticationError."""


class RejectingAuthenticator:
    """Safe production-foundation default until a local authenticator is injected."""

    def authenticate(self, auth_context: Any) -> str:
        raise AuthenticationError("AUTHENTICATION_REQUIRED")


class DeterministicFakeAuthenticator:
    """Test-only token-to-actor resolver; tokens are never persisted by Ledger."""

    def __init__(self, principals: Mapping[str, str]):
        self._principals = dict(principals)

    def authenticate(self, auth_context: Any) -> str:
        if not isinstance(auth_context, str) or auth_context not in self._principals:
            raise AuthenticationError("UNKNOWN_OR_INVALID_AUTHENTICATION")
        return self._principals[auth_context]
