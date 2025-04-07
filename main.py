import logging
from threading import Thread

from config import Config
from modules import beflaggung, ausbildungsdienst, alarmierung


def main():
	logging.basicConfig(level=logging.DEBUG, format='%(asctime)s %(threadName)s %(name)s [%(levelname)s] %(message)s')
	logging.info('Starting…')
	config = Config('config.toml')

	targets = [
		beflaggung.run,
		ausbildungsdienst.run,
		alarmierung.run,
	]
	threads = list(map(lambda target: Thread(name=f'Thread-{target.__module__}', target=target, args=(config,), daemon=True), targets))

	for thread in threads:
		logging.debug('Starting thread "%s"…', thread.name)
		thread.start()

	manually_interrupted = False
	try:
		for thread in threads:
			thread.join()
	except KeyboardInterrupt:
		manually_interrupted = True

	for thread in threads:
		if thread.is_alive():
			level = logging.DEBUG if manually_interrupted else logging.WARNING
			logging.log(level, 'Thread "%s" was still running…', thread.name)
	
	logging.info('Exiting…')

if __name__ == '__main__':
	main()
