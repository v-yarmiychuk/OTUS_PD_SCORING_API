# PYTHON_ARGCOMPLETE_OK
import argparse
import logging
import os
from http.server import HTTPServer
from typing import Any

import argcomplete

import api
from _temp.api import MainHTTPHandler
from api.configurator import Conf
from api.logger import log_format
from api.logger import logger


class Arguments:
    def __init__(self) -> None:
        self.parser = argparse.ArgumentParser(
            description='training log parser')
        self.parser.add_argument(
            '-p',
            '--port',
            required=False,
            default=8080,
            type=int,
            help='The port on which the web server will listen, by default 8080'
        )

        self.parser.add_argument(
            '--config',
            required=False,
            type=argparse.FileType(),
            help='Point to overriding config file'
        )

        argcomplete.autocomplete(self.parser)
        self.args = None
        self.parser.parse_args()

    def parse(self) -> Any:
        self.args = self.parser.parse_args()
        return self.args


def run_() -> None:
    os.chdir(os.path.join(os.path.dirname(api.__file__), os.path.pardir))
    args = Arguments().parse()
    conf = Conf(args.config)

    if conf.log_file_path:
        fh = logging.FileHandler(conf.log_file_path)
        fh.setFormatter(log_format)
        logger.addHandler(fh)

    server = HTTPServer(("localhost", args.port), MainHTTPHandler)
    logger.info("Starting server at %s" % args.port)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    server.server_close()


def run() -> None:
    try:
        run_()
    except BaseException as e:
        logger.exception(e)
        raise e
