from modules.module import Module, ModuleConfig

import logging
from threading import Thread

from config import Config
from modules import beflaggung, ausbildungsdienst, alarmierung


def main():
	config = Config('config.toml')

	logging.basicConfig(level=config.logging.level, format='%(asctime)s %(threadName)s %(name)s [%(levelname)s] %(message)s')
	logging.info('Starting…')
	logging.debug('Logging level is set to %s', logging.getLevelName(config.logging.level))

	modules: list[tuple[Module, ModuleConfig]] = [
		(beflaggung.Beflaggung('beflaggung'), beflaggung._Config()),
		(ausbildungsdienst.Ausbildungsdienst('ausbildungsdienst'), ausbildungsdienst._Config()),
		(alarmierung.Alarmierung('alarmierung'), alarmierung._Config()),
	]
	for module, cfg in modules:
		cfg.load(config.module_data(module.name), config)
		module.update_config(cfg)
	threads = list(map(lambda module: Thread(name=f'Thread-{module[0].__module__}', target=module[0].run, daemon=True), modules))

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
