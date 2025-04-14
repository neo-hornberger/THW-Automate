from functools import wraps, cache
from datetime import datetime
from threading import Lock


def parse_datetime(date: str) -> datetime:
	if date[-1] == 'Z':
		date = date[:-1] + '+00:00'
	return datetime.fromisoformat(date)

_LOCKS = {}

def synchronized(func):
	@wraps(func)
	def inner(*args, **kwargs):
		with lock:
			return func(*args, **kwargs)
	
	key = func.__qualname__
	lock = _LOCKS.get(key)
	if key not in _LOCKS:
		lock = _LOCKS[key] = Lock()

	return inner

def cached(func):
	return wraps(func)(cache(func))
