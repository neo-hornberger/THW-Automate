from .interface import IConfig, TOMLDict


class MQTTConfig(IConfig):
	host: str
	port: int
	use_ssl: bool
	username: str
	password: str
	client_id: str

	def from_toml(self, data: TOMLDict):
		self.set_value('host', data, default=None)
		self.set_value('port', data, default=1883)
		self.set_value('use_ssl', data, default=False)
		self.set_value('username', data, default=None)
		self.set_value('password', data, default=None)
		self.set_value('client_id', data, default='automation')
