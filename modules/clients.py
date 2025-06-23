from typeguard import typechecked

import logging
from paho.mqtt.client import Client as MQTTClient
from paho.mqtt.enums import CallbackAPIVersion
from caldav import DAVClient

from .utils import synchronized, cached
from lib.hermine import StashCatClient
from lib.groupalarm import GroupalarmClient


@synchronized
@cached
@typechecked
def get_hermine_client(device_id: str | None, username: str, password: str, encryption_password: str) -> StashCatClient:
	logging.info('Initializing Hermine client for user "%s"…', username)

	client = StashCatClient(device_id)
	data = client.login(username, password)
	if not data:
		raise ValueError('Login failed')
	client.open_private_key(encryption_password)

	return client

@synchronized
@cached
@typechecked
def get_groupalarm_client(api_key: str) -> GroupalarmClient:
	logging.info('Initializing Groupalarm client…')

	client = GroupalarmClient(api_key)
	client.init()

	return client

@synchronized
@cached
@typechecked
def get_mqtt_client(host: str, port: int, use_ssl: bool, username: str, password: str, client_id: str) -> MQTTClient:
	logging.info('Initializing MQTT client for user "%s"…', username)

	client = MQTTClient(CallbackAPIVersion.VERSION2, client_id)
	client.username_pw_set(username, password)
	if use_ssl:
		client.tls_set_context()
	client.connect(host, port)

	return client

@synchronized
@cached
@typechecked
def get_caldav_client(url: str, username: str, password: str) -> DAVClient:
	logging.info('Initializing CalDAV client for user "%s"…', username)

	client = DAVClient(url, username=username, password=password)
	if not client.check_cdav_support():
		raise ValueError('CalDAV server does not support required features')
	return client
