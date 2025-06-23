from .interface import IConfig, TOMLDict

class CalDAVConfig(IConfig):
	url: str
	username: str
	password: str

	def from_toml(self, data: TOMLDict) -> None:
		self.set_value('url', data, default=None)
		self.set_value('username', data, default=None)
		self.set_value('password', data, default=None)
