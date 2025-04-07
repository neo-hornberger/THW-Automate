from functools import cache
import paho.mqtt.client as mqtt
import logging

from .utils import synchronized
from lib.hermine import StashCatClient
from lib.groupalarm import GroupalarmClient


@synchronized
@cache
def get_hermine_client(device_id: str | None, username: str, password: str, encryption_password: str) -> StashCatClient:
	logging.info('Initializing Hermine client for user "%s"…', username)

	client = StashCatClient(device_id)
	data = client.login(username, password)
	if not data:
		raise ValueError('Login failed')
	client.open_private_key(encryption_password)

	return client

@synchronized
@cache
def get_groupalarm_client(api_key: str) -> GroupalarmClient:
	logging.info('Initializing Groupalarm client…')

	client = GroupalarmClient(api_key)
	client.init()

	return client

@synchronized
@cache
def get_mqtt_client(host: str, port: int, username: str, password: str, client_id: str) -> mqtt.Client:
	logging.info('Initializing MQTT client for user "%s"…', username)

	client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2, client_id)
	client.username_pw_set(username, password)
	client.tls_set_context()
	client.connect(host, port)

	return client
