"""
Centralized middleware collection for drf-common library.

This package contains all middlewares organized by functionality.
"""

# User management middlewares
from .current_user import CurrentUserMiddleware

# Debug middlewares
from .debug import DebugMiddleware, ProfilerMiddleware, SQLDebugMiddleware

__all__ = [
    # Debug middlewares
    "DebugMiddleware",
    "SQLDebugMiddleware",
    "ProfilerMiddleware",
    # User middlewares
    "CurrentUserMiddleware",
]
