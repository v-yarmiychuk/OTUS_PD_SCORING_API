import json
import logging
from http.server import BaseHTTPRequestHandler

from api.configurator import Conf
from api.method.views import MethodView


class MainHandler(BaseHTTPRequestHandler):
    router = {
        'method': MethodView
    }

    logger = logging.getLogger(f'scoring_api.MainHandler')

    def __init__(self, *args, additional_conf: Conf, **kwargs) -> None:
        self.conf = additional_conf
        super().__init__(*args, **kwargs)

    def do_POST(self) -> None:
        path = self.path.strip('/')
        self.logger.info(f'POST {path}')
        if path in self.router:
            try:
                data_string = self.rfile.read(int(self.headers['Content-Length']))
                request = json.loads(data_string)
                code, response, errors = self.router[path](conf=self.conf).post(request)

                if errors:
                    response = json.dumps({'code': code, 'errors': errors})
                else:
                    response = json.dumps({'code': code, 'response': response})

            except json.decoder.JSONDecodeError as e:
                self.logger.exception(f'Unexpected error: {e}')
                response = json.dumps({'code': self.conf.HTTP_400_BAD_REQUEST, 'error': 'JSON Decode Error'})
                code = self.conf.HTTP_400_BAD_REQUEST
            except Exception as e:
                self.logger.exception(f'Unexpected error: {e}')
                response = json.dumps({'code': self.conf.HTTP_500_INT_SERV_ERROR, 'error': 'Internal Server Error'})
                code = self.conf.HTTP_500_INT_SERV_ERROR
        else:
            response = json.dumps({'code': self.conf.HTTP_404_NOT_FOUND, 'error': f'Path {path} Not Found'})
            code = self.conf.HTTP_404_NOT_FOUND

        self.send_response(code)
        self.send_header('Content-Type', 'application/json')
        self.end_headers()
        self.wfile.write(json.dumps(response).encode('utf8'))
