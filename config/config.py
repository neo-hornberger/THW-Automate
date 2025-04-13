from typing import TypeVar
import copy
import toml

from .interface import IConfig, TOMLDict
from .logging import LoggingConfig
from .imap import IMAPConfig
from .hermine import HermineConfig
from .groupalarm import GroupalarmConfig
from .mqtt import MQTTConfig


T = TypeVar('T', bound=IConfig)
def load_toml_data(data: TOMLDict|None, cfg: type[T]|T) -> T:
	if isinstance(cfg, IConfig):
		cfg = copy.deepcopy(cfg)
	else:
		cfg = cfg()

	if data is None:
		data = {}
	
	cfg.from_toml(data)
	
	return cfg

class Config:
	logging: LoggingConfig
	imap: IMAPConfig
	hermine: HermineConfig
	groupalarm: GroupalarmConfig
	mqtt: MQTTConfig

	def __init__(self, fp):
		self._data = toml.load(fp)

		self.logging = load_toml_data(self._data.get('logging'), LoggingConfig)
		self.imap = load_toml_data(self._data.get('imap'), IMAPConfig)
		self.hermine = load_toml_data(self._data.get('hermine'), HermineConfig)
		self.groupalarm = load_toml_data(self._data.get('groupalarm'), GroupalarmConfig)
		self.mqtt = load_toml_data(self._data.get('mqtt'), MQTTConfig)

	def module_data(self, name: str) -> TOMLDict:
		return self._data.get('modules', {}).get(name, {})
