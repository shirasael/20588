import datetime
import socket
import threading
import time
from typing import Dict

from scapy.compat import raw

from common.signal_protocol import *


class Entity(object):
    def __init__(self, ip, port):
        self.ip = ip
        self.port = port

    def __repr__(self):
        return "Client<{}:{}>".format(self.ip, self.port)


music_file = r'C:\Users\Shira\Documents\20588\file_example_MP3_1MG.mp3'


class RecvClientsThread(threading.Thread):
    def __init__(self, listening_socket, on_recv_callback):
        super().__init__()
        self.listening_socket = listening_socket
        self.on_recv_callback = on_recv_callback

    def run(self):
        while True:
            try:
                conn, address = self.listening_socket.accept()
                data = conn.recv(1024)
                self.on_recv_callback(data, conn, address)
            except Exception as msg:
                print("An error occured on server thread: {}".format(msg))


class MusicServer(object):
    clients: Dict[Entity, socket.socket]

    def __init__(self, ip, port):
        self.clients = {}
        self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.server_socket.bind((ip, port))
        self.server_socket.listen(10)
        print("Accepting clients at {}:{}".format(ip, port))
        self.recv_thread = RecvClientsThread(self.server_socket,
                                             lambda _, conn, address: self.clients.update({Entity(*address): conn}))
        self.recv_thread.start()

    def signal_play_all(self):
        self._send_signal(PLAY_SIGNAL, music_file_path=music_file)

    def signal_stop_all(self):
        self._send_signal(STOP_SIGNAL)

    def _send_signal(self, signal, wait_seconds=DEFAULT_WAIT_SECONDS, music_file_path=None):
        send_time = datetime.datetime.now().timestamp()
        signal_packet = SignalPacket(signal=signal,
                                     send_timestamp=send_time,
                                     wait_seconds=wait_seconds,
                                     music_file_path=music_file_path or "")
        for entity, conn in self.clients.items():
            try:
                conn.send(raw(signal_packet))
            except Exception as msg:
                print("Could not send signal to client {}. Error: {}".format(entity, msg))


if __name__ == "__main__":
    ms = MusicServer("0.0.0.0", 12345)
    while len(ms.clients) == 0:
        continue
    ms.signal_play_all()
    time.sleep(3)
    ms.signal_stop_all()
