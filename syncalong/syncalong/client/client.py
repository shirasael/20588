import datetime
import socket

from timer import wait_for_remote_time
from common.signal_protocol import PLAY_SIGNAL, STOP_SIGNAL, SignalPacket
import vlc


class UnknownSignalException:
    def __init__(self, signal):
        self.signal = signal

    def __str__(self):
        return self.__class__.__name__ + ": " + self.signal


class Client(object):

    def __init__(self, server_ip, server_port, ntp_server):
        self.ntp_server = ntp_server
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.socket.connect((server_ip, server_port))
        self.socket.send(bytes("hello", encoding="utf-8"))
        self.media_player = None

    def start(self):
        while True:
            try:
                data = self.socket.recv(1024)
                self._handle_signal(SignalPacket(data))
            except Exception as msg:
                print("An error occurred: {}".format(msg))

    def play(self, music_file):
        print("Playing {}".format(music_file))
        self.media_player = vlc.MediaPlayer(music_file)
        self.media_player.play()

    def stop(self):
        if self.media_player is not None:
            self.media_player.stop()
        else:
            print("No music currently playing!")

    def _handle_signal(self, signal_packet):
        server_send_time = datetime.datetime.fromtimestamp(signal_packet.send_timestamp)
        delay = signal_packet.wait_seconds
        print("waiting..")
        wait_for_remote_time(server_send_time, delay, self.ntp_server)
        print("done!")
        if signal_packet.signal == PLAY_SIGNAL:
            music_file = signal_packet.music_file_path.decode('utf-8')
            self.play(music_file)
        elif signal_packet.signal == STOP_SIGNAL:
            self.stop()
        else:
            raise UnknownSignalException(signal_packet.signal)


if __name__ == "__main__":
    c = Client("localhost", 12345, '127.0.0.1')
    c.start()