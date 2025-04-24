import logging
import time
from typeguard import check_type
from typing import SupportsFloat
from schedule import Scheduler
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo

from config import Config, load_toml_data, HermineConfig, GroupalarmConfig
from modules.clients import get_hermine_client, get_groupalarm_client
from modules.utils import parse_datetime, onetime_job


class _Config:
	hermine: HermineConfig
	groupalarm: GroupalarmConfig

	scheduled_time: str
	reminder_time: timedelta
	event_filters: list[str]
	groupalarm_label: int|None
	hermine_channel: int

	def __init__(self, cfg: Config):
		data = cfg.module_data('ausbildungsdienst')

		self.hermine = load_toml_data(data.get('hermine'), cfg.hermine)
		self.groupalarm = load_toml_data(data.get('groupalarm'), cfg.groupalarm)

		self.scheduled_time = data.get('scheduled_time', '12:00')

		reminder_time = check_type(data.get('reminder_time', 10), SupportsFloat)
		self.reminder_time = timedelta(hours=float(reminder_time))

		self.event_filters = data.get('event_filters', [])
		self.groupalarm_label = data.get('groupalarm_label')
		self.hermine_channel = data['hermine_channel']


logger = logging.getLogger(__name__)


def run(cfg: Config):
	config = _Config(cfg)

	hermine = get_hermine_client(config.hermine.device_id, config.hermine.username, config.hermine.password, config.hermine.encryption_password)
	groupalarm = get_groupalarm_client(config.groupalarm.api_key)

	logger.info('Module configured successfully')

	label_persons = {}
	def _update():
		label_persons.clear()

		if config.groupalarm_label is not None:
			data = groupalarm.get_label(config.groupalarm_label)
			label_persons.update({
				user['id']: user
				for user in groupalarm.get_users()
				if user['pending'] is False and user['id'] in data['assignees']
			})
		else:
			label_persons.update({
				user['id']: user
				for user in groupalarm.get_users()
				if user['pending'] is False
			})

	def _run(timespan: timedelta) -> set[datetime]:
		event_starts = set()

		data = groupalarm.get_appointments(start=datetime.now(), end=datetime.now() + timespan, type='organization')
		events = [event for event in data if _filter_events(event, config.event_filters)]
		for event in events:
			tz = ZoneInfo(event['timezone'])
			start = parse_datetime(event['startDate']).astimezone(tz)
			end = parse_datetime(event['endDate']).astimezone(tz)

			participants = [person for person in event['participants'] if _filter_participants(person, label_persons.keys())]
			if len(participants) == 0:
				continue

			logger.info('Found event: %s %s', event['name'], start)
			event_starts.add(start)

			message = f'📅 **{event["name"]}**\n_{start:%A, %d.%m.%Y, %H:%M} – {end:%H:%M}_\n\n'
			for participant in participants:
				user = label_persons[participant['userID']]
				name = f'{user["name"]} {user["surname"]}'
				message += f'- {name:<20} {_feedbackStatus(participant)}'
				if len(participant["feedbackMessage"]) > 0:
					message += f' (_"{participant["feedbackMessage"]}"_)'
				message += '\n'
			message += '\n\n_🤖 automatically sent message_'
			
			logger.debug('Sending message to Hermine: %s', message)
			hermine.send_msg(('channel', config.hermine_channel), message, is_styled=True)
		
		return event_starts
	
	reminder_time = timedelta(hours=config.reminder_time)
	def _weekly_run():
		_update()
		event_starts = _run(timedelta(weeks=1))
		for event_start in event_starts:
			onetime_job(scheduler, (event_start - reminder_time).replace(tzinfo=None), _run, reminder_time)

	scheduler = Scheduler()
	scheduler.every().sunday.at(config.scheduled_time).do(_weekly_run)

	scheduler.run_all()
	while True:
		scheduler.run_pending()

		idle_seconds = scheduler.idle_seconds or 1
		logger.debug('Sleeping for %d seconds…', idle_seconds)
		time.sleep(idle_seconds)
	
	logger.info('Module finished!')

def _filter_events(event, filters: list[str]) -> bool:
	if len(filters) == 0:
		return True
	return event['name'] in filters

def _filter_participants(participant, filters) -> bool:
	if len(filters) == 0:
		return True
	return participant['userID'] in filters

def _feedbackStatus(participant) -> str:
	if participant['feedback'] == 0:
		return '❔'
	elif participant['feedback'] == 1:
		return '✅'
	elif participant['feedback'] == 2:
		return '❌'
	else:
		return '❗'
