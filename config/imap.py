from .interface import IConfig, TOMLDict


class IMAPConfig(IConfig):
	host: str
	port: int
	username: str
	password: str
	folder: str

	def from_toml(self, data: TOMLDict):
		self.set_value('host', data, default=None)
		self.set_value('port', data, default=993)
		self.set_value('username', data, default=None)
		self.set_value('password', data, default=None)
		self.set_value('folder', data, default='INBOX')
