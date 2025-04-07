from .interface import IConfig, TOMLDict


class HermineConfig(IConfig):
	username: str
	password: str
	encryption_password: str
	device_id: str

	def from_toml(self, data: TOMLDict) -> None:
		self.set_value('username', data)
		self.set_value('password', data)
		self.set_value('encryption_password', data)
		self.set_value('device_id', data, default='automation')
