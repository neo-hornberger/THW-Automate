from .interface import IConfig, TOMLDict


class GroupalarmConfig(IConfig):
	api_key: str

	def from_toml(self, data: TOMLDict) -> None:
		self.set_value('api_key', data, default=None)
