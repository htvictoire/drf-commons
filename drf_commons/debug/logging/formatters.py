"""
Logging formatter specifications.
"""


def get_formatters():
    """Get logging formatters configuration."""
    return {
        "verbose": {
            "format": "{levelname} {asctime} {module} {process:d} {thread:d} {funcName}:{lineno} {message}",
            "style": "{",
        },
        "minimal": {
            "format": "{levelname} {asctime} {message}",
            "style": "{",
        },
    }
