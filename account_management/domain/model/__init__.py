# from abc import ABCMeta, abstractmethod
# from itertools import count
# from functools import wraps
# import inspect


class Entity:
    def __init__(self, id, version):
        self.id = id
        self.version = version

    def __eq__(self, other):
        return other and isinstance(other, self.__class__) and self.id == other.id

    def __hash__(self):
        return hash(self.id)


class DomainEvent:
    """TODO"""
    pass

#
# class Entity(metaclass=ABCMeta):
#     """The base class of all entities.
#
#     Attributes:
#         id: A unique identifier
#         instance_id: A value unique among instances of this entity
#         version: An integer version
#         discarded: True if this entity should no longer be used, otherwise False.
#     """
#
#     _instance_id_generator = count()
#
#     class Created(DomainEvent):
#         pass
#
#     class Discarded(DomainEvent):
#         pass
#
#     @abstractmethod
#     def __init__(self, entity_id, entity_version):
#         self._id = entity_id
#         self._version = entity_version
#         self._discarded = False
#         self._instance_id = next(Entity._instance_id_generator)
#
#     def _increment_version(self):
#         self._version += 1
#
#     @property
#     def instance_id(self):
#         """A value unique among instances of this entity."""
#         return self._instance_id
#
#     @property
#     def id(self):
#         """A string unique identifier for the entity."""
#         self._check_not_discarded()
#         return self._id
#
#     @property
#     def version(self):
#         """An integer version for the entity."""
#         self._check_not_discarded()
#         return self._version
#
#     @property
#     def discarded(self):
#         """True if this entity should no longer be used, otherwise False."""
#         return self._discarded
#
#     def _check_not_discarded(self):
#         if self._discarded:
#             raise DiscardedEntityError("Attempt to use {}".format(repr(self)))
#
#
# class DiscardedEntityError(Exception):
#     """Raised when an attempt is made to use a discarded entity."""
#     pass
#
#
# def initializer(func):
#     """
#     Automatically assigns the parameters.
#
#     >>> class process:
#     ...     @initializer
#     ...     def __init__(self, cmd, reachable=False, user='root'):
#     ...         pass
#     >>> p = process('halt', True)
#     >>> p.cmd, p.reachable, p.user
#     ('halt', True, 'root')
#     """
#     names, varargs, keywords, defaults = inspect.getargspec(func)
#
#     @wraps(func)
#     def wrapper(self, *args, **kwargs):
#         for name, arg in list(zip(names[1:], args)) + list(kwargs.items()):
#             setattr(self, name, arg)
#         if names and defaults:
#             for name, default in zip(reversed(names), reversed(defaults)):
#                 if not hasattr(self, name):
#                     setattr(self, name, default)
#
#         func(self, *args, **kwargs)
#
#     return wrapper

