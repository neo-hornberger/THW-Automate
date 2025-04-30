from typeguard import typechecked
from functools import wraps, cache
from datetime import datetime, timedelta
from threading import Lock
from schedule import Job, Scheduler
from collections.abc import Callable


@typechecked
def parse_datetime(date: str) -> datetime:
	if date[-1] == 'Z':
		date = date[:-1] + '+00:00'
	return datetime.fromisoformat(date)

_LOCKS: dict[str, Lock] = {}
def synchronized(func):
	@wraps(func)
	def inner(*args, **kwargs):
		with lock:
			return func(*args, **kwargs)
	
	key = str(func.__qualname__)
	lock = _LOCKS.get(key)
	if key not in _LOCKS:
		lock = _LOCKS[key] = Lock()

	return inner

def cached(func):
	return wraps(func)(cache(func))

@typechecked
def onetime_job(scheduler: Scheduler, time: datetime, job_func: Callable, *args, **kwargs) -> Job:
	job = Job(1, scheduler).week
	job.do(job_func, *args, **kwargs)
	job.next_run = time
	job.cancel_after = time + timedelta(minutes=10)
	return job
