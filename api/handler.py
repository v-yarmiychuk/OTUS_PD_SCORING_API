import json
import logging
from http.server import BaseHTTPRequestHandler

from api.method.views import MethodView

HTTP_200_OK = 200
HTTP_400_BAD_REQUEST = 400
HTTP_403_FORBIDDEN = 403
HTTP_404_NOT_FOUND = 404
HTTP_422_UNPROCESSABLE_ENTITY = 422
HTTP_500_INTERNAL_SERVER_ERROR = 500


class MainHandler(BaseHTTPRequestHandler):
    router = {
        'method': MethodView
    }
    logger = logging.getLogger(f'scoring_api.MainHandler')

    def do_POST(self):
        response, code = {}, HTTP_200_OK
        request = None

        path = self.path.strip("/")
        self.logger.info(f'POST {path}')
        if path in self.router:
            try:
                try:
                    data_string = self.rfile.read(int(self.headers['Content-Length']))
                    request = json.loads(data_string)
                except:
                    code = HTTP_400_BAD_REQUEST
                else:
                    response, code = self.router[path](request).post()

            except Exception as e:
                self.logger.exception(f'Unexpected error: {e}')
                code = HTTP_500_INTERNAL_SERVER_ERROR
        else:
            code = HTTP_404_NOT_FOUND

        self.send_response(code)
        self.send_header("Content-Type", "application/json")
        self.end_headers()
        self.wfile.write(json.dumps(response).encode('utf8'))
