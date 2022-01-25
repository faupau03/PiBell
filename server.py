import io
import picamera
import ssl
import logging
import socketserver
from threading import Condition
from http import server
import os
import paho.mqtt.client as mqtt
import paho.mqtt.publish as publish

from queue import Queue
from struct import pack, calcsize
from datetime import datetime


class StreamingOutput(object):
    def __init__(self):
        self.frame = None
        self.buffer = io.BytesIO()
        self.condition = Condition()

    def write(self, buf):
        if buf.startswith(b'\xff\xd8'):
            # New frame, copy the existing buffer's content and notify all
            # clients it's available
            self.buffer.truncate()
            with self.condition:
                self.frame = self.buffer.getvalue()
                self.condition.notify_all()
            self.buffer.seek(0)
        return self.buffer.write(buf)

class StreamingHandler(server.BaseHTTPRequestHandler):
    def do_GET(self):
        if self.path == '/':
            self.send_response(200)
            self.send_header('Age', 0)
            self.send_header('Cache-Control', 'no-cache, private')
            self.send_header('Pragma', 'no-cache')
            self.send_header('Content-Type', 'multipart/x-mixed-replace; boundary=FRAME')
            self.end_headers()
            try:
                while True:
                    with output.condition:
                        output.condition.wait()
                        frame = output.frame
                    self.wfile.write(b'--FRAME\r\n')
                    self.send_header('Content-Type', 'image/jpeg')
                    self.send_header('Content-Length', len(frame))
                    self.end_headers()
                    self.wfile.write(frame)
                    self.wfile.write(b'\r\n')
            except Exception as e:
                logging.warning(
                    'Removed streaming client %s: %s',
                    self.client_address, str(e))
        elif self.path == '/open':
            client.publish("homeassistant/pibell/state", "ON")
            self.send_response(200)
        else:
            self.send_error(404)
            self.end_headers()



# The callback for when the client receives a CONNACK response from the server.
def on_connect(client, userdata, flags, rc):
    print("Connected with result code "+str(rc))
    # Send discovery message to homeassistant
    client.publish("homeassistant/binary_sensor/pibell/config", '{"name": "pibell", "device_class": "binary_sensor", "state_topic": "homeassistant/binary_sensor/pibell/state"}')

# The callback for when a PUBLISH message is received from the server.
def on_message(client, userdata, msg):
    print(msg.topic+" "+str(msg.payload))

client = mqtt.Client()
client.on_connect = on_connect
client.on_message = on_message
mqtt_host = "192.168.178.52"
mqtt_port = 1883
if (os.getenv('MQTT_HOST')):
    mqtt_host = os.getenv('MQTT_HOST')
if (os.getenv('MQTT_PORT')):
    mqtt_port = int(os.getenv('MQTT_PORT'))
client.connect(os.environ.get("MQTT_HOST"), os.environ.get("MQTT_PORT"), 60)





class StreamingServer(socketserver.ThreadingMixIn, server.HTTPServer):
    allow_reuse_address = True
    daemon_threads = True

with picamera.PiCamera(resolution='640x480', framerate=24) as camera:
    output = StreamingOutput()
    camera.start_recording(output, format='mjpeg')
    try:
        address = ('', os.environ.get('VIDEO_PORT', 8000))
        server = StreamingServer(address, StreamingHandler)
        server.socket = ssl.wrap_socket(server.socket,
                                        server_side=True,
                                        certfile=os.path.join(os.path.abspath(os.path.dirname(__file__)) + '/cert.pem'),
                                        keyfile=os.path.join(os.path.abspath(os.path.dirname(__file__)) + '/key.pem'),
                                        ssl_version=ssl.PROTOCOL_TLS)
        server.serve_forever()
        client.loop_forever()
    finally:
        camera.stop_recording()
