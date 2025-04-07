from typing import TypeAlias
import datetime


TOMLDict: TypeAlias = dict[str, "TOMLData"]
TOMLData: TypeAlias = TOMLDict|list["TOMLData"]|str|int|float|bool|datetime.datetime|datetime.date|datetime.time

class IConfig:
	def from_toml(self, data: TOMLDict) -> None:
		raise NotImplementedError
	
	def set_value(self, attr_name: str, data: TOMLDict, *, key: str|None = None, default: TOMLData|None = None) -> None:
		key = key or attr_name
		setattr(self, attr_name, data.get(key, getattr(self, attr_name, default)))
