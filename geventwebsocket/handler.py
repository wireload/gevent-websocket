import re
import struct
import time
import traceback
import sys
from hashlib import md5
from gevent.pywsgi import WSGIHandler
from geventwebsocket import WebSocket

class WebSocketHandler(WSGIHandler):
    def __init__(self, *args, **kwargs):
        self.websocket_connection = False
        super(WebSocketHandler, self).__init__(*args, **kwargs)

    def handle_one_response(self):
        # In case the client doesn't want to initialize a WebSocket connection
        # we will proceed with the default PyWSGI functionality.
        if self.environ.get("HTTP_CONNECTION") != "Upgrade" or \
           self.environ.get("HTTP_UPGRADE") != "WebSocket" or \
           not self.environ.get("HTTP_ORIGIN"):
            return super(WebSocketHandler, self).handle_one_response()
        else:
            self.websocket_connection = True

        self.websocket = WebSocket(self.rfile, self.wfile, self.socket, self.environ)
        self.environ['wsgi.websocket'] = self.websocket

        # Detect the Websocket protocol
        if "HTTP_SEC_WEBSOCKET_KEY1" in self.environ:
            version = 76
        else:
            version = 75

        if version == 75:
            headers = [
                ("Upgrade", "WebSocket"),
                ("Connection", "Upgrade"),
                ("WebSocket-Origin", self.websocket.origin),
                ("WebSocket-Protocol", self.websocket.protocol),
                ("WebSocket-Location", "ws://" + self.environ.get('HTTP_HOST') + self.websocket.path),
            ]
            self.start_response("101 Web Socket Protocol Handshake", headers)
        elif version == 76:
            challenge = self._get_challenge()
            headers = [
                ("Upgrade", "WebSocket"),
                ("Connection", "Upgrade"),
                ("Sec-WebSocket-Origin", self.websocket.origin),
                ("Sec-WebSocket-Protocol", self.websocket.protocol),
                ("Sec-WebSocket-Location", "ws://" + self.environ.get('HTTP_HOST') + self.websocket.path),
            ]

            self.start_response("101 Web Socket Protocol Handshake", headers)
            self.write([challenge])
        else:
            raise Exception("Version not supported")

        return self.application(self.environ, self.start_response)

    def write(self, data):
        if self.websocket_connection:
            self.wfile.writelines(data)
        else:
            super(WebSocketHandler, self).write(data)

    def start_response(self, status, headers, exc_info=None):
        if self.websocket_connection:
            self.status = status

            towrite = []
            towrite.append('%s %s\r\n' % (self.request_version, self.status))

            for header in headers:
                towrite.append("%s: %s\r\n" % header)

            towrite.append("\r\n")
            self.wfile.writelines(towrite)
            self.headers_sent = True
        else:
            super(WebSocketHandler, self).start_response(status, headers, exc_info)

    def _get_key_value(self, key_value):
        key_number = int(re.sub("\\D", "", key_value))
        spaces = re.subn(" ", "", key_value)[1]

        if key_number % spaces != 0:
            raise HandShakeError("key_number %d is not an intergral multiple of"
                                 " spaces %d" % (key_number, spaces))

        return key_number / spaces

    def _get_challenge(self):
        key1 = self.environ.get('HTTP_SEC_WEBSOCKET_KEY1')
        key2 = self.environ.get('HTTP_SEC_WEBSOCKET_KEY2')

        if not (key1 and key2):
            message = "Client using old/invalid protocol implementation"
            headers = [("Content-Length", str(len(message))),]
            self.start_response("400 Bad Request", headers)
            self.write([message])
            self.close_connection = True
            return

        part1 = self._get_key_value(self.environ['HTTP_SEC_WEBSOCKET_KEY1'])
        part2 = self._get_key_value(self.environ['HTTP_SEC_WEBSOCKET_KEY2'])

        # This request should have 8 bytes of data in the body
        key3 = self.rfile.read(8)

        challenge = ""
        challenge += struct.pack("!I", part1)
        challenge += struct.pack("!I", part2)
        challenge += key3

        return md5(challenge).digest()
