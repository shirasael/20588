import socket
import threading
import time
from typing import List
from datetime import datetime

from common.general_packet import GeneralPacket
from syncalong.common.length_socket import LengthSocket, send_to_all
from syncalong.common.signal_packet import *
from syncalong.common.file_sync_packet import *


class RecvClientsThread(threading.Thread):
    def __init__(self, listening_socket, on_recv_callback):
        super().__init__()
        self.listening_socket = listening_socket
        self.on_recv_callback = on_recv_callback
        self.should_stop = False

    def run(self):
        while not self.should_stop:
            try:
                conn, address = self.listening_socket.accept()
                data = conn.recv()
                self.on_recv_callback(data, conn, address)
            except (Exception, socket.error) as e:
                print(f"An error occured on server thread: {e}")

    def stop(self):
        self.should_stop = True


class MusicServer(object):
    clients: List[LengthSocket]

    def __init__(self, ip, port, max_clients=10):
        self.clients = []
        self.server_socket = LengthSocket(socket.AF_INET, socket.SOCK_STREAM)
        self.server_socket.bind((ip, port))
        self.server_socket.listen(max_clients)
        print(f"Accepting clients at {ip}:{port}")
        self.recv_thread = RecvClientsThread(self.server_socket,
                                             lambda data, conn, addr: self.clients.append(conn))

    def start(self):
        self.recv_thread.should_stop = False
        if not self.recv_thread.is_alive():
            self.recv_thread.start()

    def signal_play_all(self, music_file):
        print("Signal play")
        self._send_signal(PLAY_SIGNAL, music_file_name=os.path.basename(music_file))

    def signal_stop_all(self):
        print("Signal stop")
        self._send_signal(STOP_SIGNAL)

    def serve_music_file(self, local_file_path: str):
        print(f"Sending file {local_file_path}")
        missing_clients = self.query_file_existence(local_file_path)
        send_to_all(missing_clients, send_file_data(local_file_path))

    def query_file_existence(self, local_file_path: str) -> List[LengthSocket]:
        """
        Check which of the clients have the given file in their repository.
        :param local_file_path: File to look for in clients.
        :return: List of all the clients that don't have the required file and should be synced.
        """
        who_has = who_has_packet(local_file_path)
        missing_clients = []
        for conn in self.clients:
            print(f"{conn} has {local_file_path}?")
            try:
                conn.send_packet(who_has)
                ans = GeneralPacket(conn.recv())[FileSyncPacket]
                if ans.message_type == MISSING:
                    missing_clients.append(conn)
                    print(f"Sending file to {conn}")
            except (Exception, socket.error) as e:
                print(f"Could not check {conn}: {e}")
        return missing_clients

    def _send_signal(self, signal, wait_seconds=DEFAULT_WAIT_SECONDS, music_file_name=None):
        send_time = datetime.now().timestamp()
        signal_packet = SignalPacket(signal=signal,
                                     send_timestamp=send_time,
                                     wait_seconds=wait_seconds,
                                     music_file_name=music_file_name or "")
        for conn in self.clients:
            try:
                conn.send_packet(signal_packet)
            except (Exception, socket.error) as e:
                print(f"Could not send signal to {conn}: {e}")

    def stop(self):
        self.recv_thread.stop()


if __name__ == "__main__":
    music_file = r'C:\Users\Shira\Documents\20588\file_example_MP3_1MG.mp3'
    ms = MusicServer("0.0.0.0", 22222)
    ms.start()
    while True:
        while len(ms.clients) == 0:
            continue
        ms.serve_music_file(music_file)
        ms.signal_play_all(music_file)
        time.sleep(3)
        ms.signal_stop_all()
        ms.clients = []
