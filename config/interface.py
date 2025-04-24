from __future__ import annotations

from typing import TypeAlias, Any
from typeguard import typechecked
from collections.abc import Callable
import datetime


TOMLDict: TypeAlias = dict[str, "TOMLData"]
TOMLData: TypeAlias = TOMLDict|list["TOMLData"]|str|int|float|bool|datetime.datetime|datetime.date|datetime.time

@typechecked
class IConfig:
	def from_toml(self, data: TOMLDict) -> None:
		raise NotImplementedError
	
	def set_value(self, attr_name: str, data: TOMLDict, *, key: str|None = None, default: TOMLData|None = None, converter: Callable[[Any], Any] = lambda x: x) -> None:
		key = key or attr_name
		try:
			value = converter(data[key])
		except KeyError:
			value = getattr(self, attr_name, default)
		setattr(self, attr_name, value)
