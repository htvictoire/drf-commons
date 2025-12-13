"""
Custom model fields.
"""

import warnings

from django.conf import settings as django_settings
from django.db import models
from django.utils.translation import gettext_lazy as _

from drf_commons.current_user.utils import get_current_authenticated_user
from drf_commons.utils.middleware_checker import require_middleware


class CurrentUserField(models.ForeignKey):
    """
    Model field that automatically sets the current user.

    This field automatically populates with the current authenticated user
    when creating or updating model instances (if on_update=True).
    """

    warning = (
        "You passed an argument to CurrentUserField that will be "
        "ignored. Avoid args and following kwargs: default, null, to."
    )
    description = _("as default value sets the current logged in user if available")
    defaults = dict(
        null=True,
        default=get_current_authenticated_user,
        to=django_settings.AUTH_USER_MODEL,
    )

    @require_middleware(
        "drf_commons.middlewares.current_user.CurrentUserMiddleware", "CurrentUserField"
    )
    def __init__(self, *args, **kwargs):
        self.on_update = kwargs.pop("on_update", False)

        # If `to` is present in kwargs, and the same when ignoring case then
        # update `to` to use the defaults. This allows using e.g.
        # `to='auth.User'` or `to='AUTH.USER'` and have it normalized to
        # `to='auth.User'`.
        if "to" in kwargs and kwargs["to"].lower() == self.defaults["to"].lower():
            kwargs["to"] = self.defaults["to"]

        self._warn_for_shadowing_args(*args, **kwargs)

        if "on_delete" not in kwargs:
            kwargs["on_delete"] = models.CASCADE

        if self.on_update:
            kwargs["editable"] = False
            kwargs["blank"] = True

        kwargs.update(self.defaults)
        super(CurrentUserField, self).__init__(**kwargs)

    def deconstruct(self):
        name, path, args, kwargs = super(CurrentUserField, self).deconstruct()
        if self.on_update:
            kwargs["on_update"] = self.on_update
            del kwargs["editable"]
            del kwargs["blank"]

        return name, path, args, kwargs

    def pre_save(self, model_instance, add):
        if self.on_update:
            value = get_current_authenticated_user()
            if value is not None:
                value = value.pk
            setattr(model_instance, self.attname, value)
            return value
        else:
            return super(CurrentUserField, self).pre_save(model_instance, add)

    def _warn_for_shadowing_args(self, *args, **kwargs):
        if args:
            warnings.warn(self.warning)
        else:
            for key in set(kwargs).intersection(set(self.defaults.keys())):
                if not kwargs[key] == self.defaults[key]:
                    warnings.warn(self.warning)
                    break
