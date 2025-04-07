from .interface import IConfig, TOMLDict


class MQTTConfig(IConfig):
	host: str
	port: int
	username: str
	password: str
	client_id: str

	def from_toml(self, data: TOMLDict):
		self.set_value('host', data)
		self.set_value('port', data, default=1883)
		self.set_value('username', data)
		self.set_value('password', data)
		self.set_value('client_id', data, default='automation')
