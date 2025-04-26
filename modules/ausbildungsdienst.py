from typing import SupportsFloat
from collections.abc import Iterator

import time
from schedule import Scheduler
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo

from config import Config, load_toml_data, HermineConfig, GroupalarmConfig, TOMLDict
from modules.module import ModuleConfig, Module
from modules.clients import get_hermine_client, get_groupalarm_client
from modules.utils import parse_datetime, onetime_job


class _Config(ModuleConfig):
	hermine: HermineConfig
	groupalarm: GroupalarmConfig

	scheduled_time: str
	reminder_time: timedelta
	event_filters: list[str]
	groupalarm_label: int|None
	hermine_channel: int

	def load(self, data: TOMLDict, cfg: Config) -> None:
		self.hermine = load_toml_data(data.get('hermine'), cfg.hermine)
		self.groupalarm = load_toml_data(data.get('groupalarm'), cfg.groupalarm)

		self.set_value('scheduled_time', data, default='12:00')
		self.set_value('reminder_time', data, default=timedelta(hours=10), converter=self._conv_remtime)
		self.set_value('event_filters', data, default=[])
		self.set_value('groupalarm_label', data, default=None)
		self.set_value('hermine_channel', data)
	
	def _conv_remtime(self, remtime: SupportsFloat) -> timedelta:
		return timedelta(hours=float(remtime))


class Ausbildungsdienst(Module[_Config]):

	def init(self) -> None:
		self.hermine = get_hermine_client(self.config.hermine.device_id, self.config.hermine.username, self.config.hermine.password, self.config.hermine.encryption_password)
		self.groupalarm = get_groupalarm_client(self.config.groupalarm.api_key)

		self.label_persons = {}
		self.scheduler = Scheduler()

	def run(self) -> None:
		self.scheduler.every().sunday.at(self.config.scheduled_time).do(self._weekly_run)

		self.scheduler.run_all()
		while True:
			self.scheduler.run_pending()

			idle_seconds = self.scheduler.idle_seconds or 1
			self.logger.debug('Sleeping for %d seconds…', idle_seconds)
			time.sleep(idle_seconds)
		
		self.logger.info('Module finished!')

	def _run(self, timespan: timedelta) -> set[datetime]:
		event_starts = set()

		data = self.groupalarm.get_appointments(start=datetime.now(), end=datetime.now() + timespan, type='organization')
		for event in self._filter_events(data):
			event_start = self._handle_event(event)
			if event_start is not None:
				event_starts.add(event_start)
		
		return event_starts
	
	def _weekly_run(self):
		self._update_labels()
		event_starts = self._run(timedelta(weeks=1))
		for event_start in event_starts:
			onetime_job(self.scheduler, (event_start - self.config.reminder_time).replace(tzinfo=None), self._run, self.config.reminder_time)
	
	def _update_labels(self) -> None:
		self.label_persons.clear()

		if self.config.groupalarm_label is not None:
			data = self.groupalarm.get_label(self.config.groupalarm_label)
			self.label_persons.update({
				user['id']: user
				for user in self.groupalarm.get_users()
				if user['pending'] is False and user['id'] in data['assignees']
			})
		else:
			self.label_persons.update({
				user['id']: user
				for user in self.groupalarm.get_users()
				if user['pending'] is False
			})
	
	def _handle_event(self, event) -> datetime|None:
		tz = ZoneInfo(event['timezone'])
		start = parse_datetime(event['startDate']).astimezone(tz)
		end = parse_datetime(event['endDate']).astimezone(tz)

		participants = self._filter_participants(event['participants'])
		if len(participants) == 0:
			return None

		self.logger.info('Found event: %s %s', event['name'], start)

		message = f'📅 **{event["name"]}**\n_{start:%A, %d.%m.%Y, %H:%M} – {end:%H:%M}_\n\n'
		for participant in participants:
			user = self.label_persons[participant['userID']]
			name = f'{user["name"]} {user["surname"]}'
			message += f'- {name:<20} {_feedbackStatus(participant)}'
			if len(participant["feedbackMessage"]) > 0:
				message += f' (_"{participant["feedbackMessage"]}"_)'
			message += '\n'
		message += '\n\n_🤖 automatically sent message_'
		
		self.logger.debug('Sending message to Hermine: %s', message)
		self.hermine.send_msg(('channel', self.config.hermine_channel), message, is_styled=True)

		return start

	def _filter_events(self, events: list) -> Iterator:
		filters = self.config.event_filters
		if len(filters) == 0:
			return iter(events)
		return (event for event in events if event['name'] in filters)

	def _filter_participants(self, participants: list) -> list:
		filters = self.label_persons.keys()
		if len(filters) == 0:
			return participants
		return [person for person in participants if person['userID'] in filters]

def _feedbackStatus(participant) -> str:
	if participant['feedback'] == 0:
		return '❔'
	elif participant['feedback'] == 1:
		return '✅'
	elif participant['feedback'] == 2:
		return '❌'
	else:
		return '❗'
