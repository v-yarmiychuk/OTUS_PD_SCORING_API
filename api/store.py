import logging
import time
from random import random
from typing import Any
from typing import Union

import redis

from api.configurator import Conf


class KVStore:
    def __init__(self,
                 conf: Union[Conf, None] = None,
                 host: str = '127.0.0.1',
                 port: int = 6379,
                 db: int = 0
                 ) -> None:

        self.conf = conf
        self.reconnect_try = True
        self.reconnect_attempt = 5
        self.reconnect_timeout = 1
        self.reconnect_smart_delay = True

        if self.conf is not None:
            self.host = self.conf.redis_host
            self.port = self.conf.redis_port
            self.db = self.conf.redis_db
            self.reconnect_try = self.conf.redis_reconnect_try
            self.reconnect_attempt = self.conf.redis_reconnect_attempt
            self.reconnect_timeout = self.conf.redis_reconnect_timeout
            self.reconnect_smart_delay = self.conf.redis_reconnect_smart_delay

        self.host = host
        self.port = port
        self.db = db

        self.logger = logging.getLogger(f'log_analyzer.Store')

        self.pool: Union[redis.ConnectionPool, None] = None
        self.server: Union[redis.Redis, None] = None

        self._get_server()

    def _get_server(self):
        self.logger.info(f'try to redis connect')
        self.pool = None
        self.server = None
        _error = False
        try:
            self.pool = redis.ConnectionPool(
                host=self.host,
                port=self.port,
                db=self.db,
                decode_responses=True
            )
            self.server = redis.Redis(
                connection_pool=self.pool,
                socket_timeout=0.5,
                socket_connect_timeout=0.5,
                retry_on_timeout=False,
                health_check_interval=10
            )
            self.server.ping()
        except redis.exceptions.ConnectionError as e:
            self.logger.error(f"Redis connection - ConnectionError {e}")
            _error = True
        except redis.exceptions.ResponseError as e:
            self.logger.error(f"Redis connection - ResponseError {e}")
            _error = True

        if _error:
            if self.reconnect_try and self.reconnect_attempt > 0:
                self.reconnect_attempt -= 1

                self.logger.error(f'waiting for reconnection after {self.reconnect_timeout} seconds ')
                time.sleep(self.reconnect_timeout)

                if self.reconnect_smart_delay:
                    self.reconnect_timeout = self.reconnect_timeout * 2 + random()

                self._get_server()
            else:
                raise redis.exceptions.ConnectionError

    def get(self, key) -> Any:
        try:
            val = self.server.get(name=key)
        except redis.exceptions.ConnectionError as e:
            self.logger.error(f"Redis connection - ConnectionError {e}")
            val = None

        return val

    def set(self, key, val, ex: Union[int, None] = None):
        try:
            self.server.set(name=key, value=val, ex=ex)
        except redis.exceptions.ConnectionError as e:
            self.logger.error(f"Redis connection - ConnectionError {e}")

    def __getitem__(self, key) -> Any:
        return self.get(key)

    def __setitem__(self, key, val):
        self.set(key, val)
