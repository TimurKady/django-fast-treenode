# -*- coding: utf-8 -*-
"""
TreeeNodeModel Class Decorators

- Decorator `@cached_method` for caching method results.

Version: 3.0.0
Author: Timur Kady
Email: timurkady@yandex.com
"""


_TIMEOUT = 10
_INTERVAL = 0.2

_UNSET = object()


class classproperty(object):
    """Classproperty class."""

    def __init__(self, getter):
        """Init."""
        self.getter = getter

    def __get__(self, instance, owner):
        """Get."""
        return self.getter(owner)


def lazy_property(source, default=_UNSET):
    """
    Декоратор ленивого свойства, которое берёт значение из другого поля.

    source — имя поля (например, 'parent_id')
    default — значение по умолчанию. Если не задан, берётся self.source
    """
    def decorator(func):
        def getter(self):
            attr_name = '_' + func.__name__
            if not hasattr(self, attr_name):
                if default is _UNSET:
                    value = getattr(self, source)
                else:
                    value = default
                setattr(self, attr_name, value)
            return getattr(self, attr_name)

        def setter(self, value):
            attr_name = '_' + func.__name__
            setattr(self, attr_name, value)

        return property(getter, setter)
    return decorator
