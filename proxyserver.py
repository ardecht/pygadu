from logger import create_logger
from http.server import BaseHTTPRequestHandler, HTTPServer
from urllib.parse import parse_qs

logger = create_logger("ProxyServer")


class ProxyHandler(BaseHTTPRequestHandler):
    addr = ""

    def write_response(self, code=200, headers=None, content=""):
        if headers is None:
            headers = {}

        self.send_response(code)

        for hK, hV in headers.items():
            self.send_header(hK, hV)

        self.end_headers()
        self.wfile.write(bytes(content, "utf-8"))

    def log_request(self, code='-', size='-'):
        if code == 200:
            logger.debug("[{}] [{}] {}".format(self.command, code, self.path))
        else:
            logger.error("[{}] [{}] {} - NOT IMPLEMENTED".format(self.command, code, self.path))

    def do_GET(self):
        self.resolve_request()

    def do_POST(self):
        self.resolve_request()

    def do_CONNECT(self):
        # self.write_response(200, {"Connection": "keep-alive"}, "")
        pass

    def resolve_request(self):
        if self.path.startswith("http://appmsg.gadu-gadu.pl/appsvc/appmsg_ver8.asp"):
            self.write_response(200, {}, "0 0 " + self.addr + ":8074 " + self.addr + "\r\n")

        elif self.path.startswith("http://adserver.gadu-gadu.pl"):
            self.write_response(200, {"Content-Type": "text/html; charset=UTF-8"},
                                "<center><strong>pyGadu</strong></center>\r\n")

        elif self.path.startswith("http://api.gadu-gadu.pl/request_token"):
            self.write_response(200, {"Content-Type": "text/xml"},
                                "<!--?xml version=\"1.0\"?--><result><oauth_token>0</oauth_token><oauth_token_secret>0</oauth_token_secret><status>0</status></result>")

        elif self.path.startswith("http://register.gadu-gadu.pl/appsvc/regtoken.asp"):
            self.write_response(200, {"Content-Type": "text/html; charset=UTF-8"},
                                "115 30 6 32e66999ae2c409b36225a0f400b6353 http://register.gadu-gadu.pl/regRndPictNew.php")

        elif self.path.startswith("http://register.gadu-gadu.pl/fmregister.php"):
            content_len = int(self.headers.get('content-length', 0))
            post_body = self.rfile.read(content_len)
            post = parse_qs(post_body, keep_blank_values=1)
            self.write_response(200, {"Content-Type": "text/html; charset=UTF-8"}, "reg_success:{}".format(str(post[b"tokenval"][0], 'utf-8')))

        else:
            self.write_response(404)


class ProxyServer:
    def __init__(self, addr, port):
        self.addr = addr
        self.port = port
        self.server = HTTPServer((self.addr, self.port), ProxyHandler)
        ProxyHandler.addr = addr
        pass

    def listen(self):
        try:
            logger.info("Server is listening at {}:{}".format(self.addr, self.port))
            self.server.serve_forever()
            logger.error("Server stopped.")
        except Exception as e:
            logger.critical("Proxy server exception! {}".format(e))
