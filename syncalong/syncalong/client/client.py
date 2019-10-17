import datetime
import os
import socket
import vlc

from common.general_packet import GeneralPacket, handle_packet
from syncalong.client.timer import wait_for_remote_time

from syncalong.common.length_socket import LengthSocket
from syncalong.common.file_sync_packet import FileSyncPacket, WHO_HAS, who_has_answer_packet, FILE_SEND
from syncalong.common.signal_packet import PLAY_SIGNAL, STOP_SIGNAL, SignalPacket


class UnknownSignalException:
    def __init__(self, signal):
        self.signal = signal

    def __str__(self):
        return self.__class__.__name__ + ": " + self.signal


class Client(object):

    def __init__(self, server_ip, server_port, ntp_server, music_files_repo):
        self.ntp_server = ntp_server
        self.music_files_repo = music_files_repo
        self.socket = LengthSocket(socket.AF_INET, socket.SOCK_STREAM)
        self.socket.connect((server_ip, server_port))
        self.media_player = None

    def start(self):
        self.socket.send(bytes("hello", encoding="utf-8"))
        while True:
            try:
                recv_packet = GeneralPacket(self.socket.recv())
                handle_packet(recv_packet, {
                    SignalPacket: self._handle_signal,
                    FileSyncPacket: self._handle_file_sync
                })
            except Exception as msg:
                print("An error occurred: {}".format(msg))

    def play(self, music_file_path):
        print("Playing {}".format(music_file_path))
        self.media_player = vlc.MediaPlayer(music_file_path)
        self.media_player.play()

    def stop(self):
        if self.media_player is not None:
            print("Stopping music")
            self.media_player.stop()
        else:
            print("No music currently playing!")

    def _handle_signal(self, signal_packet):
        print("Got signal {}".format(signal_packet.signal))
        server_send_time = datetime.datetime.fromtimestamp(signal_packet.send_timestamp)
        delay = signal_packet.wait_seconds
        wait_for_remote_time(server_send_time, delay, self.ntp_server)
        if signal_packet.signal == PLAY_SIGNAL:
            music_file = signal_packet.music_file_name.decode('utf-8')
            local_music_file_path = os.path.join(self.music_files_repo, music_file)
            self.play(local_music_file_path)
        elif signal_packet.signal == STOP_SIGNAL:
            self.stop()
        else:
            raise UnknownSignalException(signal_packet.signal)

    def _handle_file_sync(self, file_sync_packet):
        local_path = os.path.join(self.music_files_repo, file_sync_packet.file_name.decode('utf-8'))
        if file_sync_packet.message_type == WHO_HAS:
            print("Got who has!")
            send_packet = who_has_answer_packet(local_path, file_sync_packet.file_size)
            self.socket.send_packet(send_packet)
        elif file_sync_packet.message_type == FILE_SEND:
            file_size = file_sync_packet.file_size
            received = 0
            with open(local_path, 'wb') as local_file:
                while received < file_size:
                    data = self.socket.recv()
                    received += len(data)
                    local_file.write(data)


if __name__ == "__main__":
    c = Client("localhost", 22222, '127.0.0.1', r'C:\temp\syncalong')
    c.start()
