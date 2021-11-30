import logging
from typing import Any
from typing import Dict
from typing import List
from typing import Tuple

from api.configurator import Conf


class BaseView:
    def __init__(self, conf: Conf) -> None:
        self.conf = conf
        self.validator = None
        self.request = None
        self.logger = logging.getLogger(f'scoring_api.View')

    def get(self) -> Tuple[int, Any, List[str]]:
        raise NotImplemented

    def post(self, request: Dict) -> Tuple[int, Any, List[str]]:
        raise NotImplemented
