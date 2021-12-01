import datetime
import functools
import hashlib
import os
import unittest

import api
from api.configurator import Conf
from api.method.views import MethodView


def cases(cases_items):
    def decorator(f):
        @functools.wraps(f)
        def wrapper(*args):
            for c in cases_items:
                new_args = args + (c if isinstance(c, tuple) else (c,))
                f(*new_args)

        return wrapper

    return decorator


class TestSuite(unittest.TestCase):
    def setUp(self):
        self.conf = Conf()

    def get_response(self, request):
        return MethodView(conf=self.conf).post(request)

    def set_valid_auth(self, request):
        if request.get("login") == self.conf.admin_login:
            line = self.conf.admin_login + str(self.conf.admin_salt)
        else:
            line = request.get("account", "") + request.get("login", "") + self.conf.salt

        request["token"] = hashlib.sha512(line.encode('utf-8')).hexdigest()

    def test_empty_request(self):
        code, response, errors = self.get_response({})
        self.assertEqual(self.conf.HTTP_422_UNPROCESSABLE_ENTITY, code)

    @cases([
        {"account": "horns&hoofs", "login": "h&f", "method": "online_score", "token": "", "arguments": {}},
        {"account": "horns&hoofs", "login": "h&f", "method": "online_score", "token": "sdd", "arguments": {}},
        {"account": "horns&hoofs", "login": "admin", "method": "online_score", "token": "", "arguments": {}},
    ])
    def test_bad_auth(self, request):
        code, response, errors = self.get_response(request)
        self.assertEqual(self.conf.HTTP_403_FORBIDDEN, code)

    @cases([
        {"account": "horns&hoofs", "login": "h&f", "method": "online_score"},
        {"account": "horns&hoofs", "login": "h&f", "arguments": {}},
        {"account": "horns&hoofs", "method": "online_score", "arguments": {}},
    ])
    def test_invalid_method_request(self, request):
        self.set_valid_auth(request)
        code, response, errors = self.get_response(request)
        self.assertEqual(self.conf.HTTP_422_UNPROCESSABLE_ENTITY, code)
        self.assertTrue(len(errors))

    @cases([
        {},
        {"phone": "79175002040"},
        {"phone": "89175002040", "email": "stupnikov@otus.ru"},
        {"phone": "79175002040", "email": "stupnikovotus.ru"},
        {"phone": "79175002040", "email": "stupnikov@otus.ru", "gender": -1},
        {"phone": "79175002040", "email": "stupnikov@otus.ru", "gender": "1"},
        {"phone": "79175002040", "email": "stupnikov@otus.ru", "gender": 1, "birthday": "01.01.1890"},
        {"phone": "79175002040", "email": "stupnikov@otus.ru", "gender": 1, "birthday": "XXX"},
        {"phone": "79175002040", "email": "stupnikov@otus.ru", "gender": 1, "birthday": "01.01.2000", "first_name": 1},
        {"phone": "79175002040", "email": "stupnikov@otus.ru", "gender": 1, "birthday": "01.01.2000",
         "first_name": "s", "last_name": 2},
        {"phone": "79175002040", "birthday": "01.01.2000", "first_name": "s"},
        {"email": "stupnikov@otus.ru", "gender": 1, "last_name": 2},
    ])
    def test_invalid_score_request(self, arguments):
        request = {"account": "horns&hoofs", "login": "h&f", "method": "online_score", "arguments": arguments}
        self.set_valid_auth(request)
        code, response, errors = self.get_response(request)
        self.assertEqual(self.conf.HTTP_422_UNPROCESSABLE_ENTITY, code, (arguments, errors))
        self.assertTrue(len(errors))

    @cases([
        {"phone": "79175002040", "email": "stupnikov@otus.ru"},
        {"phone": 79175002040, "email": "stupnikov@otus.ru"},
        {"gender": 2, "birthday": "01.01.2000", "first_name": "a", "last_name": "b"},
        {"gender": 1, "birthday": "01.01.2000"},
        {"gender": 3, "birthday": "01.01.2000"},
        {"first_name": "a", "last_name": "b"},
        {"phone": "79175002040", "email": "stupnikov@otus.ru", "gender": 1, "birthday": "01.01.2000",
         "first_name": "a", "last_name": "b"},
    ])
    def test_ok_score_request(self, arguments):
        request = {"account": "horns&hoofs", "login": "h&f", "method": "online_score",
                   "arguments": arguments}
        self.set_valid_auth(request)
        code, response, errors = self.get_response(request)
        self.assertEqual(self.conf.HTTP_200_OK, code, (request, errors))
        score = response.get("score")
        self.assertTrue(isinstance(score, (int, float)) and score >= 0, (arguments, score, errors))

    def test_ok_score_admin_request(self):
        arguments = {"phone": "79175002040", "email": "stupnikov@otus.ru"}
        request = {"account": "horns&hoofs", "login": self.conf.admin_login, "method": "online_score",
                   "arguments": arguments}
        self.set_valid_auth(request)
        code, response, errors = self.get_response(request)
        self.assertEqual(self.conf.HTTP_200_OK, code, (request, errors))
        score = response.get("score")
        self.assertEqual(score, 42)

    @cases([
        {"client_ids": [1, 2, 3], "date": datetime.datetime.today().strftime("%d.%m.%Y")},
        {"client_ids": [1, 2], "date": "19.07.2017"},
        {"client_ids": [0]},
    ])
    def test_ok_interests_request(self, arguments):
        request = {"account": "horns&hoofs", "login": "h&f", "method": "clients_interests",
                   "arguments": arguments}
        self.set_valid_auth(request)
        code, response, errors = self.get_response(request)
        self.assertEqual(self.conf.HTTP_200_OK, code, (arguments, errors))
        self.assertEqual(len(arguments["client_ids"]), len(response))
        self.assertTrue(all(v and isinstance(v, list) and all(isinstance(i, str) for i in v)
                            for v in response.values()))

    @cases([
        {},
        {"date": "20.07.2017"},
        {"client_ids": [], "date": "20.07.2017"},
        {"client_ids": {1: 2}, "date": "20.07.2017"},
        {"client_ids": ["1", "2"], "date": "20.07.2017"},
        {"client_ids": [1, 2], "date": "XXX"},
    ])
    def test_invalid_interests_request(self, arguments):
        request = {"account": "horns&hoofs", "login": "h&f", "method": "clients_interests", "arguments": arguments}
        self.set_valid_auth(request)
        code, response, errors = self.get_response(request)
        self.assertEqual(self.conf.HTTP_422_UNPROCESSABLE_ENTITY, code, (arguments, errors))
        self.assertTrue(len(errors))


if __name__ == "__main__":
    os.chdir(os.path.join(os.path.dirname(api.__file__), os.path.pardir))
    unittest.main()
