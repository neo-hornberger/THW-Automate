import logging

from .interface import IConfig, TOMLDict


class LoggingConfig(IConfig):
	level: int

	def from_toml(self, data: TOMLDict) -> None:
		self.set_value('level', data, default=logging.INFO, converter=logging.getLevelName)
