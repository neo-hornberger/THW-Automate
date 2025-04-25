from __future__ import annotations

from typing import TypeAlias, TypeVar, NewType, final
from typeguard import typechecked, check_type
from abc import ABCMeta, abstractmethod
from collections.abc import Callable
import datetime


TOMLDict: TypeAlias = dict[str, "TOMLData"]
TOMLData: TypeAlias = TOMLDict|list["TOMLData"]|str|int|float|bool|datetime.datetime|datetime.date|datetime.time

X = TypeVar('X')

Unknown = NewType('Unknown', object)
NOT_GIVEN = Unknown(object)

@typechecked
class IConfig(metaclass=ABCMeta):

	@abstractmethod
	def from_toml(self, data: TOMLDict) -> None:
		...
	
	@final
	def set_value(self, attr_name: str, data: TOMLDict, *, key: str|None = None, default: X|None|Unknown = NOT_GIVEN, converter: Callable[[TOMLData], X] = lambda x: x) -> None:
		key = key or attr_name
		required = default is NOT_GIVEN
		try:
			value = converter(data[key])
		except KeyError:
			if required and not hasattr(self, attr_name):
				raise
			value = check_type(getattr(self, attr_name, default), X|None)
		setattr(self, attr_name, value)
