import logging.config
from typing import Any
from typing import Optional
from typing import TextIO

import yaml


class Conf:
    config = {}
    default_config_path = 'configs/default_config.yaml'

    def __init__(self, stream: Optional[TextIO]) -> None:
        self.logger = logging.getLogger(f'log_analyzer.Conf')

        with open(Conf.default_config_path, 'r') as f:
            self._load_config(f, default=True)

        if stream:
            self._load_config(stream)

    def _load_config(self, stream: TextIO, default: bool = False) -> None:
        data = yaml.safe_load(stream)
        for key, value in data.items():
            if default:
                self.config[key] = value
            else:
                if key not in self.config:
                    self.logger.error(f'Unknown parameter received: {key}')
                    continue
                if self.config.get(key) == value:
                    continue
                self.logger.info(f'Applying a configuration parameter: {key}: {value}')
                self.config[key] = value

    def __getattribute__(self, name: str) -> Any:
        if name in Conf.config.keys():
            return self.config[name]
        else:
            return object.__getattribute__(self, name)
