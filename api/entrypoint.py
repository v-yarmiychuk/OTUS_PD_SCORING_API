import argparse
import logging
import os
from http.server import HTTPServer
from typing import Any, Tuple

import argcomplete

import api
from api.configurator import Conf
from api.handler import MainHandler
from api.logger import log_format
from api.logger import logger


class Arguments:
    def __init__(self) -> None:
        self.parser = argparse.ArgumentParser(
            description='training log parser')
        self.parser.add_argument(
            "-l",
            "--listen",
            default="localhost",
            help="Specify the IP address on which the server listens",
        )
        self.parser.add_argument(
            "-p",
            "--port",
            type=int,
            default=8000,
            help="Specify the port on which the server listens",
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


class ConfHTTPServer(HTTPServer):
    def __init__(self, *args, additional_conf: Conf, **kwargs) -> None:
        self.additional_conf = additional_conf
        super().__init__(*args, **kwargs)

    def finish_request(self, request: bytes, client_address: Tuple[str, int]) -> None:
        self.RequestHandlerClass(request, client_address, self, additional_conf=self.additional_conf)


def run_() -> None:
    os.chdir(os.path.join(os.path.dirname(api.__file__), os.path.pardir))
    args = Arguments().parse()
    conf = Conf(args.config)

    if conf.log_file_path:
        fh = logging.FileHandler(conf.log_file_path)
        fh.setFormatter(log_format)
        logger.addHandler(fh)

    server = ConfHTTPServer((args.listen, args.port), MainHandler, additional_conf=conf)
    logger.info(f'Starting server at {args.listen}:{args.port}')

    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass

    server.server_close()
    logger.info(f'Closing server.')


def run() -> None:
    try:
        run_()
    except BaseException as e:
        raise e


if __name__ == '__main__':
    run()
