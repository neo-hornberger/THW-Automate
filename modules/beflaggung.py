from typeguard import check_type
from imap_tools.mailbox import BaseMailBox
from imap_tools.message import MailMessage

import time
import re
import requests
from imap_tools import MailBox, AND, consts
from icalevents import icalevents
from datetime import time as dtime, timedelta
from astral import Degrees, Elevation, Observer, sun

from config import Config, load_toml_data, IMAPConfig, HermineConfig, TOMLDict
from modules.module import ModuleConfig, Module
from modules.clients import get_hermine_client


class _Config(ModuleConfig):
	imap: IMAPConfig
	hermine: HermineConfig

	filter_from: list[str]
	location: tuple[Degrees, Degrees, Elevation]|None
	hermine_channel: int

	max_con_time: int
	idle_timeout: int
	recon_delay: int

	def load(self, data: TOMLDict, cfg: Config) -> None:
		self.imap = load_toml_data(data.get('imap'), cfg.imap)
		self.hermine = load_toml_data(data.get('hermine'), cfg.hermine)

		self.set_value('filter_from', data, default=[])
		self.set_value('location', data, converter=self._conv_loc)
		self.set_value('hermine_channel', data)
		self.set_value('max_con_time', data, default=29 * 60)
		self.set_value('idle_timeout', data, default=3 * 60)
		self.set_value('recon_delay', data, default=60)
	
	def _conv_loc(self, loc: TOMLDict) -> tuple[Degrees, Degrees, Elevation]|None:
		if loc.get('latitude') is not None and loc.get('longitude') is not None:
			return (
				check_type(loc['latitude'], Degrees),
				check_type(loc['longitude'], Degrees),
				check_type(loc.get('elevation', 0), Elevation),
			)
		else:
			return None


TIMEZONE = 'Europe/Berlin'
EARLIEST_START_TIME = dtime(7, 0)


class Beflaggung(Module[_Config]):

	def init(self) -> None:
		self.hermine = get_hermine_client(self.config.hermine.device_id, self.config.hermine.username, self.config.hermine.password, self.config.hermine.encryption_password)

		self.observer = Observer(latitude=self.config.location[0], longitude=self.config.location[1], elevation=self.config.location[2]) if self.config.location is not None else None

	def run(self) -> None:
		def _run(mailbox: BaseMailBox):
			for msg in mailbox.fetch(AND(from_=self.config.filter_from, seen=False), charset='utf-8', mark_seen=False):
				found_event = self._handle_msg(msg)

				if found_event:
					mailbox.flag(msg.uid, consts.MailMessageFlags.SEEN, True)

		done = False
		while not done:
			con_start_time = time.monotonic()
			con_live_time = 0.0

			try:
				with MailBox(self.config.imap.host, self.config.imap.port).login(self.config.imap.username, self.config.imap.password, self.config.imap.folder) as mailbox:
					self.logger.debug('new connection')

					# fetch messages that have been received while the connection was down
					_run(mailbox)

					while con_live_time < self.config.max_con_time:
						try:
							responses = mailbox.idle.wait(timeout=self.config.idle_timeout)

							self.logger.debug('IDLE responses: %s', responses)

							if len(responses) > 0:
								_run(mailbox)

							con_live_time = time.monotonic() - con_start_time
						except KeyboardInterrupt:
							done = True
							break
			except Exception as e:
				self.logger.error('Error: %s\nreconnect in %d seconds…', e, self.config.recon_delay)
				time.sleep(self.config.recon_delay)
		
		self.logger.info('Module finished!')
	
	def _handle_msg(self, msg: MailMessage) -> bool:
		self.logger.info('found message: %s %s %s', msg.subject, msg.from_, msg.date)

		ics_url = re.search(r'<a href="(([^"]+)\?view=renderBMIWebICS)"', msg.html)
		if ics_url is None:
			self.logger.warning('No ICS URL found in message: %s', msg.subject)
			return False

		ics = requests.get(ics_url.group(1)).text
		events = icalevents.events(string_content=ics, start=msg.date, end=msg.date + timedelta(days=365))

		if len(events) > 0:
			event = events[0]

			if event.url is None:
				event.url = ics_url.group(2)

			message = f'📅 **{event.summary}**\n_{event.start:%A, %d.%m.%Y}_'

			if self.observer is not None:
				date = event.start.date()
				start = max(sun.sunrise(self.observer, date, TIMEZONE).time(), EARLIEST_START_TIME)
				end = sun.sunset(self.observer, date, TIMEZONE)
				message += f' _({start:%H:%M} – {end:%H:%M})_'

			message += f'\n\n{event.description}\n\n{event.url}'
			message += '\n\n_🤖 automatically sent message_'
			
			self.logger.debug('Sending message to Hermine: %s', message)
			self.hermine.send_msg(('channel', self.config.hermine_channel), message, is_styled=True)

		return True
