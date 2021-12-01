import hashlib
import json
import random
from typing import Any
from typing import Dict
from typing import List
from typing import Tuple
from typing import Union

from api.base.views import BaseView
from api.configurator import Conf
from api.method.validators import ClientsInterestsValidator
from api.method.validators import MethodValidator
from api.method.validators import OnlineScoreValidator
from api.store import KVStore


class MethodView(BaseView):
    def __init__(self, conf: Conf) -> None:
        self.methods_handlers = {
            'online_score': self.method_online_score,
            'clients_interests': self.method_clients_interests
        }
        self.store = KVStore(conf)
        super().__init__(conf)

    def post(self, request: Dict) -> Tuple[int, Any, List[str]]:
        status, errors = MethodValidator(conf=self.conf).validate(request)
        if not status:
            return self.conf.HTTP_422_UNPROCESSABLE_ENTITY, None, errors

        if not self.check_auth(request):
            return self.conf.HTTP_403_FORBIDDEN, None, ['Forbidden']

        handler = self.methods_handlers.get(request.get('method', ''), None)

        if handler is not None:
            # noinspection PyArgumentList
            return handler(data=request)
        else:
            return self.conf.HTTP_422_UNPROCESSABLE_ENTITY, None, ['the requested method is not defined']

    def check_auth(self, request: Dict) -> bool:
        account = request.get('account', '')
        login = request.get('login', '')
        token = request.get('token', '')

        if login == self.conf.admin_login:
            line = self.conf.admin_login + str(self.conf.admin_salt)
        else:
            line = account + login + self.conf.salt

        digest = hashlib.sha512(line.encode('utf-8')).hexdigest()
        if digest == token:
            self.logger.info(f'{login} - authentication passed')
            return True

        self.logger.info(f'{login} - authentication failed')
        return False

    def method_online_score(self, data: Dict) -> Tuple[int, Any, Union[List[str], None]]:
        arguments = data.get('arguments', {})
        status, errors = OnlineScoreValidator(conf=self.conf).validate(arguments)

        if not status:
            return self.conf.HTTP_422_UNPROCESSABLE_ENTITY, None, errors

        if data.get('login', '') == self.conf.admin_login:
            score = 42
        else:
            score = self.get_score(**arguments)

        return self.conf.HTTP_200_OK, {'score': score}, None

    def method_clients_interests(self, data: Dict) -> Tuple[int, Any, Union[List[str], None]]:
        arguments = data.get('arguments', {})
        status, errors = ClientsInterestsValidator(conf=self.conf).validate(arguments)

        if not status:
            return self.conf.HTTP_422_UNPROCESSABLE_ENTITY, None, errors

        result = {client: self.get_interests(client) for client in arguments.get('client_ids')}

        return self.conf.HTTP_200_OK, result, None

    def get_score(self, phone=None, email=None, birthday=None, gender=None, first_name=None, last_name=None):
        key_parts = [
            first_name or '',
            last_name or '',
            phone or '',
            birthday if birthday is not None else '',
        ]
        key_parts = [str(item) for item in key_parts]
        line = ''.join(key_parts).encode('utf-8')
        key = 'uid:' + hashlib.md5(line).hexdigest()

        score = self.store[key] or 0

        if score:
            return float(score)

        if phone:
            score += 1.5
        if email:
            score += 1.5
        if birthday and gender:
            score += 1.5
        if first_name and last_name:
            score += 0.5

        self.store.set(key, score, 60 * 60)
        return score

    def get_interests(self, cid: int) -> List[str]:
        interests = ['cars', 'pets', 'travel', 'hi-tech', 'sport', 'music', 'books', 'tv', 'cinema', 'geek', 'otus']
        key = f'i:{cid}'
        val = self.store.get(key)

        if val is None:
            val = random.sample(interests, 2)
            self.store.set(key, json.dumps(val), 60 * 60)
        else:
            val = json.loads(val)

        return val
