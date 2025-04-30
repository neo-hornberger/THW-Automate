from abc import ABCMeta, abstractmethod
from typing import final

import logging

from config import IConfig, TOMLDict, Config


class ModuleConfig(IConfig):

	@final
	def from_toml(self, data: TOMLDict) -> None:
		raise NotImplementedError('from_toml() should not be called directly')

	@abstractmethod
	def load(self, data: TOMLDict, cfg: Config) -> None:
		...

class Module[T: ModuleConfig](metaclass=ABCMeta):
	def __init__(self, name: str, *, config: T|None = None):
		self.name = name

		self.logger = logging.getLogger(f'modules.{name}')

		if config is not None:
			self.update_config(config)

	@final
	def update_config(self, config: T) -> None:
		self.config = config

		self.init()

		self.logger.info('Module configured successfully')
	
	@abstractmethod
	def init(self) -> None:
		...

	@abstractmethod
	def run(self) -> None:
		...
