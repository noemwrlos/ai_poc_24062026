from threading import Lock

class SingletonMetaNoArgs(type):
    """
    Singleton metaclass for classes without parameters on constructor,
    for compatibility with FastApi Depends() function.
    """

    _instances = {}

    _lock: Lock = Lock()

    def __call__(cls):
        with cls._lock:
            if cls not in cls._instances:
                instance = super().__call__()
                cls._instances[cls] = instance
        return cls._instances[cls]