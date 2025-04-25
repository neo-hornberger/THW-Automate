import json
import mgrs
from paho.mqtt.client import Client as MQTTClient, MQTTMessage

from config import Config, load_toml_data, HermineConfig, MQTTConfig, TOMLDict
from modules.module import ModuleConfig, Module
from modules.clients import get_hermine_client, get_mqtt_client
from modules.utils import parse_datetime


class _Config(ModuleConfig):
	hermine: HermineConfig
	mqtt: MQTTConfig

	topic: str
	groupalarm_label: int|None
	hermine_channel: int

	def load(self, data: TOMLDict, cfg: Config) -> None:
		self.hermine = load_toml_data(data.get('hermine'), cfg.hermine)
		self.mqtt = load_toml_data(data.get('mqtt'), cfg.mqtt)

		self.set_value('topic', data)
		self.set_value('groupalarm_label', data, default=None)
		self.set_value('hermine_channel', data)


class Alarmierung(Module[_Config]):

	def init(self) -> None:
		self.hermine = get_hermine_client(self.config.hermine.device_id, self.config.hermine.username, self.config.hermine.password, self.config.hermine.encryption_password)
		self.mqtt = get_mqtt_client(self.config.mqtt.host, self.config.mqtt.port, self.config.mqtt.use_ssl, self.config.mqtt.username, self.config.mqtt.password, self.config.mqtt.client_id)

	def run(self) -> None:
		@self.mqtt.connect_callback()
		def _(client: MQTTClient, userdata, connect_flags, reason_code, properties):
			if reason_code == 0:
				self.logger.debug('Successfully connected to MQTT broker at "%s:%d"', client.host, client.port)
			else:
				self.logger.error(f'Failed to connect to MQTT broker: {reason_code}')
			
			client.subscribe(self.config.topic)
		
		@self.mqtt.message_callback()
		def _(client: MQTTClient, userdata, msg: MQTTMessage):
			data = json.loads(msg.payload.decode())
			time = parse_datetime(data['event']['startDate'])

			opt_content = data.get('optionalContent')
			location = None
			if opt_content is not None:
				lat = float(opt_content['latitude'])
				lon = float(opt_content['longitude'])
				location = (
					lat,
					lon,
					opt_content['address'],
					_format_mgrs(lat, lon),
				)
			
			self.logger.info('Received message for event: %s', data['event']['name'])

			message = f'🚨 **{data["event"]["name"]}**\n_{data["event"]["severity"]["icon"]} {data["event"]["severity"]["name"]}_\n\n{data["message"]}'
			if location is not None:
				message += f'\n\n_{location[2]}_\n_{location[3]}_\n_{location[0]}°N {location[1]}°O_'
			message += '\n\n_🤖 automatically sent message_'

			self.logger.debug('Sending message to Hermine: %s', message)
			self.hermine.send_msg(('channel', self.config.hermine_channel), message, location=location, is_styled=True)

		self.mqtt.loop_forever(retry_first_connection=True)

		self.logger.info('Module finished!')

def _format_mgrs(lat: float, lon: float, precision: int = 5) -> str:
	if precision < 0 or precision > 5:
		raise ValueError('Precision must be between 0 and 5.')

	coords = mgrs.MGRS().toMGRS(lat, lon, MGRSPrecision=precision)

	return f'{coords[0:5]} {coords[5:5+precision]} {coords[5+precision:]}'
