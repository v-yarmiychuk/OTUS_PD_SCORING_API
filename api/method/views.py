class MethodView:

    def __init__(self, request) -> None:
        self.request = request

    def post(self):
        return self.request, 200
