import functools
import os
import unittest

import redis

import api
from api.configurator import Conf
from api.store import KVStore


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

    @cases([
        ['test_key', 'test_value', None],
        ['test_key', 'test_value', 10],
        ['test_key', '', None],
        ['test_key', 0, None],
        ['test_key', -10, None],
        ['test_key', 0.1, None],
    ])
    def test_set_valid_kv(self, arguments):
        store = KVStore(conf=self.conf)
        key, val, ex = arguments
        store.set(key, val, ex)

    @cases([
        ['test_key', 'test_value', -10],
        ['', 'test_value', 0],
    ])
    def test_set_invalid_kv(self, arguments):
        store = KVStore(conf=self.conf)
        key, val, ex = arguments

        with self.assertRaises(redis.exceptions.ResponseError):
            store.set(key, val, ex)

    @cases([
        ['test_key', 'test_value', None],
        ['test_key', 'test_value', 100],
    ])
    def test_get_valid_kv(self, arguments):
        store = KVStore(conf=self.conf)
        key, val, ex = arguments
        store.set(key, val, ex)
        self.assertEqual(val, store.get(key), arguments)


if __name__ == "__main__":
    os.chdir(os.path.join(os.path.dirname(api.__file__), os.path.pardir, os.path.pardir))
    unittest.main()
