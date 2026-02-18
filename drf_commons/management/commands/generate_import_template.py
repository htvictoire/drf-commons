"""
Expose the import-template generator command at the Django app root.

Keeping the command import here ensures Django discovers it when only
``drf_commons`` is present in ``INSTALLED_APPS``.
"""

from drf_commons.services.management.commands.generate_import_template import Command

