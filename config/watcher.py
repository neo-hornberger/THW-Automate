from collections.abc import Callable
from watchdog.events import DirModifiedEvent, FileModifiedEvent

from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler


class ConfigWatcher:
	def __init__(self, path: str):
		self.observer = Observer()
		self.observer.schedule(_EventHandler(self), path, recursive=False)
		self.observer.start()

	def on_change(self, handler: Callable[[], None]) -> None:
		self._on_change = handler

class _EventHandler(FileSystemEventHandler):
	def __init__(self, watcher: ConfigWatcher):
		self.watcher = watcher

	def on_modified(self, event: DirModifiedEvent|FileModifiedEvent) -> None:
		if event.is_directory:
			return
		self.watcher._on_change()
