from config import Config, load_toml_data, HermineConfig, TOMLDict
from modules.module import ModuleConfig, Module
from modules.clients import get_hermine_client

from lib.hermine import unpaginate


class _Config(ModuleConfig):
	hermine: HermineConfig

	prefix: str
	hermine_channel: int

	def load(self, data: TOMLDict, cfg: Config) -> None:
		self.hermine = load_toml_data(data.get('hermine'), cfg.hermine)

		self.set_value('prefix', data, default='!')
		self.set_value('hermine_channel', data)


class UserInterface(Module[_Config]):
	
	def init(self) -> None:
		self.hermine = get_hermine_client(self.config.hermine.device_id, self.config.hermine.username, self.config.hermine.password, self.config.hermine.encryption_password)

	def run(self) -> None:
		socket = self.hermine.get_socket()

		@socket.on('message_sync')
		def _(data):
			if (
				data['kind'] != 'message' or
				data['type'] != 'text' or
				data['text'] is None
			):
				return
			if data['channel_id'] not in [self.config.hermine_channel]:
				return
			
			msg = next(filter(lambda msg: msg['id'] == data['id'], self.hermine.get_messages(('channel', data['channel_id']))))
			text = str(msg['text'] if msg['encrypted'] is False else msg['text_decrypted']).strip()

			if text.startswith(self.config.prefix):
				cmd, *args = text[len(self.config.prefix):].split(None)
				self._handle_command(cmd.lower(), args, data['sender'], data['channel'])

		socket.wait()

		self.logger.info('Module finished!')
	
	def _handle_command(self, command: str, args: list[str], user, channel) -> None:
		self.logger.debug('Received command "%s" with args %s from user "%s %s" in channel #%s', command, args, user['first_name'], user['last_name'], channel['name'])
