from modules.module import Module, ModuleConfig

import logging
from threading import Thread

from config import Config, ConfigWatcher
from modules import beflaggung, ausbildungsdienst, alarmierung


CONFIG_FILE = 'config.toml'


def main():
	config = load_config(CONFIG_FILE)

	logging.basicConfig(level=config.logging.level, format='%(asctime)s %(threadName)s %(name)s [%(levelname)s] %(message)s')
	logging.info('Starting…')
	logging.debug('Logging level is set to %s', logging.getLevelName(config.logging.level))

	modules: list[tuple[Module, ModuleConfig]] = [
		(beflaggung.Beflaggung('beflaggung'), beflaggung._Config()),
		(ausbildungsdienst.Ausbildungsdienst('ausbildungsdienst'), ausbildungsdienst._Config()),
		(alarmierung.Alarmierung('alarmierung'), alarmierung._Config()),
	]
	update_config(config, modules)
	threads = list(map(lambda module: Thread(name=f'Thread-{module[0].__module__}', target=module[0].run, daemon=True), modules))

	for thread in threads:
		logging.debug('Starting thread "%s"…', thread.name)
		thread.start()

	config_watcher = ConfigWatcher(CONFIG_FILE)
	def on_config_change():
		nonlocal config
		logging.info('Config file change detected…')
		cfg = load_config(CONFIG_FILE, config)
		if cfg == config:
			logging.debug('Config is unchanged, skipping reload')
			return
		config = cfg
		update_config(config, modules)
	config_watcher.on_change(handler=on_config_change)

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

def load_config(fp, default: Config|None = None) -> Config:
	try:
		return Config(fp)
	except Exception as e:
		msg = 'Failed to load config file "%s"'
		if default is None:
			logging.error(msg, fp)
			raise
		else:
			logging.warning(f'{msg}: %s', fp, e.args[0])
			return default

def update_config(config: Config, modules: list[tuple[Module, ModuleConfig]]) -> None:
	for module, cfg in modules:
		cfg.load(config.module_data(module.name), config)
		module.update_config(cfg)


if __name__ == '__main__':
	main()
