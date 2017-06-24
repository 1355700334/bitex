from functools import wraps
from .exceptions import UnsupportedEndpointError

#@wraps
def check_compatibility(**version_func_pairs):
    """This Decorator maker takes any number of
    version_num=[list of compatible funcs] pairs, and checks if the
    decorated function is compatible with the currently set API version.
    Should this not be the case, an UnsupportedEndpointError is raised.

    If the api version required contains '.', replace this with an
    underscore ('_') - the decorator will take care of it.
    """

    def decorator(func):
        def wrapped(*args, **kwargs):
            interface = args[0]
            for version, methods in version_func_pairs.items():
                if func.__name__ in methods:
                    if version.replace('_', '.') != interface.REST.version:
                        error_msg = ("Method not available on this API version"
                                    "(current is %s, supported is %s)" %
                                    (interface.REST.version,
                                     version.replace('_', '.')))
                        raise UnsupportedEndpointError(error_msg)

            return func(*args, **kwargs)
        return wrapped
    return decorator
