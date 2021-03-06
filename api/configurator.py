import logging.config
import os
from typing import Any
from typing import Optional
from typing import TextIO

import yaml


class Conf:
    config = {}
    default_config_path = 'configs/default_config.yaml'

    def __init__(self, stream: Optional[TextIO] = None, load_def_conf: bool = True, ) -> None:

        self.logger = logging.getLogger(f'scoring_api.Conf')
        self.load_def_conf = load_def_conf

        if load_def_conf:
            self._load_default_config()

        if stream:
            self._load_config(stream, force=False if load_def_conf else True)

    def _load_default_config(self) -> None:
        path = os.path.join(
            os.path.dirname(os.path.abspath(__file__)),
            os.path.pardir,
            Conf.default_config_path
        )
        with open(path, 'r') as f:
            self._load_config(f, force=True)

    def _load_config(self, stream: TextIO, force: bool = False) -> None:
        data = yaml.safe_load(stream)
        for key, value in data.items():
            if force:
                self.config[key] = value
            else:
                if key not in self.config:
                    self.logger.error(f'Unknown parameter received: {key}')
                    continue
                if self.config.get(key) == value:
                    continue
                self.logger.info(f'Applying a configuration parameter: {key}: {value}')
                self.config[key] = value

    def __getattr__(self, name: str) -> Any:
        if name in Conf.config.keys():
            return self.config[name]
        else:
            raise AttributeError(f'Attribute "{name}" was not defined.')
