from tornado.web import RequestHandler, HTTPError


class NotFoundHandler(RequestHandler):
    def prepare(self):  # for all methods
        raise HTTPError(
            status_code=404,
            reason="Invalid resource path."
        )
