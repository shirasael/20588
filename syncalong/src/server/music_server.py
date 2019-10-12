import socket
import threading
import time
from typing import Dict

from common.consts import PLAY_SIGNAL, STOP_SIGNAL


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
        for entity, conn in self.clients.items():
            try:
                conn.send(PLAY_SIGNAL + bytes(music_file, encoding="utf-8"))
            except Exception as msg:
                print("Could not signal client {} to play. Error: {}".format(entity, msg))

    def signal_stop_all(self):
        for entity, conn in self.clients.items():
            try:
                conn.send(STOP_SIGNAL)
            except Exception as msg:
                print("Could not signal client {}. Error: {}".format(entity, msg))


if __name__ == "__main__":
    ms = MusicServer("0.0.0.0", 12345)
    while len(ms.clients) == 0:
        continue
    ms.signal_play_all()
    time.sleep(3)
    ms.signal_stop_all()
