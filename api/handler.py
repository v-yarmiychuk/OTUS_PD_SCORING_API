import json
import logging
from http.server import BaseHTTPRequestHandler
from http import HTTPStatus
from api.configurator import Conf
from api.method.views import MethodView


class MainHandler(BaseHTTPRequestHandler):
    router = {
        'method': MethodView
    }

    logger = logging.getLogger(f'scoring_api.MainHandler')

    def __init__(self, *args, conf: Conf, **kwargs) -> None:
        self.conf = conf
        super().__init__(*args, **kwargs)

    def do_POST(self) -> None:
        path = self.path.strip('/')
        self.logger.info(f'POST {path}')
        if path in self.router:
            try:
                data_string = self.rfile.read(int(self.headers['Content-Length']))

                try:
                    request = json.loads(data_string)
                except json.decoder.JSONDecodeError as e:
                    self.logger.exception(f'Unexpected error: {e} \nreceived data: {data_string}')
                    response = json.dumps({'code': HTTPStatus.BAD_REQUEST, 'error': 'JSON Decode Error'})
                    code = HTTPStatus.BAD_REQUEST
                else:
                    code, response, errors = self.router[path](conf=self.conf).post(request)

                    if errors:
                        response = json.dumps({'code': code, 'errors': errors})
                    else:
                        response = json.dumps({'code': code, 'response': response})

            except Exception as e:
                self.logger.exception(f'Unexpected error: {e}')
                response = json.dumps({'code': HTTPStatus.INTERNAL_SERVER_ERROR, 'error': 'Internal Server Error'})
                code = HTTPStatus.INTERNAL_SERVER_ERROR
        else:
            response = json.dumps({'code': HTTPStatus.NOT_FOUND, 'error': f'Path {path} Not Found'})
            code = HTTPStatus.NOT_FOUND

        self.send_response(code)
        self.send_header('Content-Type', 'application/json')
        self.end_headers()
        self.wfile.write(json.dumps(response).encode('utf8'))
