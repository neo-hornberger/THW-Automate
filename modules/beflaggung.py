import logging
import time
import re
import requests
from imap_tools import MailBox, AND, consts
from icalevents import icalevents
from datetime import timedelta

from config import Config, load_toml_data, IMAPConfig, HermineConfig
from modules.clients import get_hermine_client


class _Config:
	imap: IMAPConfig
	hermine: HermineConfig

	filter_from: list[str]
	hermine_channel: int

	max_con_time: int
	idle_timeout: int
	recon_delay: int

	def __init__(self, cfg: Config):
		data = cfg.module_data('beflaggung')

		self.imap = load_toml_data(data.get('imap'), cfg.imap)
		self.hermine = load_toml_data(data.get('hermine'), cfg.hermine)

		self.filter_from = data.get('filter_from', [])
		self.hermine_channel = data['hermine_channel']

		self.max_con_time = data.get('max_con_time', 29 * 60)
		self.idle_timeout = data.get('idle_timeout', 3 * 60)
		self.recon_delay = data.get('recon_delay', 60)


logger = logging.getLogger(__name__)


def run(cfg: Config):
	config = _Config(cfg)

	hermine = get_hermine_client(config.hermine.device_id, config.hermine.username, config.hermine.password, config.hermine.encryption_password)

	logger.info('Module configured successfully')

	done = False
	while not done:
		con_start_time = time.monotonic()
		con_live_time = 0.0

		try:
			with MailBox(config.imap.host, config.imap.port).login(config.imap.username, config.imap.password, config.imap.folder) as mailbox:
				logger.debug('new connection')

				while con_live_time < config.max_con_time:
					try:
						responses = mailbox.idle.wait(timeout=config.idle_timeout)

						logger.debug('IDLE responses: %s', responses)

						if len(responses) > 0:
							for msg in mailbox.fetch(AND(from_=config.filter_from, seen=False), charset='utf-8', mark_seen=False):
								logger.info('found message: %s %s %s', msg.subject, msg.from_, msg.date)

								ics_url = re.search(r'<a href="(([^"]+)\?view=renderBMIWebICS)"', msg.html)
								if ics_url is None:
									logger.warning('No ICS URL found in message: %s', msg.subject)
									continue

								ics = requests.get(ics_url.group(1)).text
								events = icalevents.events(string_content=ics, start=msg.date, end=msg.date + timedelta(days=365))

								if len(events) > 0:
									event = events[0]

									if event.url is None:
										event.url = ics_url.group(2)

									message = f'📅 **{event.summary}**\n_{event.start:%A, %d.%m.%Y}_\n\n{event.description}\n\n{event.url}'
									message += '\n\n_🤖 automatically sent message_'
									
									logger.debug('Sending message to Hermine: %s', message)
									hermine.send_msg(('channel', config.hermine_channel), message, is_styled=True)

								mailbox.flag(msg.uid, consts.MailMessageFlags.SEEN, True)

						con_live_time = time.monotonic() - con_start_time
					except KeyboardInterrupt:
						done = True
						break
		except Exception as e:
			logger.error('Error: %s\nreconnect in %d seconds…', e, config.recon_delay)
			time.sleep(config.recon_delay)
	
	logger.info('Module finished!')
