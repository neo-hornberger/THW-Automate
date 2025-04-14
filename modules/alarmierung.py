import logging
import json
import mgrs
from paho.mqtt.client import Client as MQTTClient, MQTTMessage

from config import Config, load_toml_data, HermineConfig, MQTTConfig
from modules.clients import get_hermine_client, get_mqtt_client
from modules.utils import parse_datetime


class _Config:
	hermine: HermineConfig
	mqtt: MQTTConfig

	topic: str
	groupalarm_label: int|None
	hermine_channel: int

	def __init__(self, cfg: Config):
		data = cfg.module_data('alarmierung')

		self.hermine = load_toml_data(data.get('hermine'), cfg.hermine)
		self.mqtt = load_toml_data(data.get('mqtt'), cfg.mqtt)

		self.topic = data['topic']
		self.groupalarm_label = data.get('groupalarm_label')
		self.hermine_channel = data['hermine_channel']


logger = logging.getLogger(__name__)


def run(cfg: Config):
	config = _Config(cfg)

	hermine = get_hermine_client(config.hermine.device_id, config.hermine.username, config.hermine.password, config.hermine.encryption_password)
	mqtt = get_mqtt_client(config.mqtt.host, config.mqtt.port, config.mqtt.use_ssl, config.mqtt.username, config.mqtt.password, config.mqtt.client_id)

	logger.info('Module configured successfully')

	def _run(data: dict):
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
		
		logger.info('Received message for event: %s', data['event']['name'])

		message = f'🚨 **{data["event"]["name"]}**\n_{data["event"]["severity"]["icon"]} {data["event"]["severity"]["name"]}_\n\n{data["message"]}'
		if location is not None:
			message += f'\n\n_{location[2]}_\n_{location[3]}_\n_{location[0]}°N {location[1]}°O_'
		message += '\n\n_🤖 automatically sent message_'

		logger.debug('Sending message to Hermine: %s', message)
		hermine.send_msg(('channel', config.hermine_channel), message, location=location, is_styled=True)

	@mqtt.connect_callback()
	def _(client: MQTTClient, userdata, connect_flags, reason_code, properties):
		if reason_code == 0:
			logger.debug('Successfully connected to MQTT broker at "%s:%d"', client.host, client.port)
		else:
			logger.error(f'Failed to connect to MQTT broker: {reason_code}')
		
		client.subscribe(config.topic)
	
	@mqtt.message_callback()
	def _(client: MQTTClient, userdata, msg: MQTTMessage):
		_run(json.loads(msg.payload.decode()))

	mqtt.loop_forever(retry_first_connection=True)

	logger.info('Module finished!')

def _format_mgrs(lat: float, lon: float, precision: int = 5) -> str:
	if precision < 0 or precision > 5:
		raise ValueError('Precision must be between 0 and 5.')

	coords = mgrs.MGRS().toMGRS(lat, lon, MGRSPrecision=precision)

	return f'{coords[0:5]} {coords[5:5+precision]} {coords[5+precision:]}'
