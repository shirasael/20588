import socket

from common.signal_protocol import PLAY_SIGNAL, STOP_SIGNAL
import vlc


class Client(object):

    def __init__(self, server_ip, server_port):
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.socket.connect((server_ip, server_port))
        self.socket.send(bytes("hello", encoding="utf-8"))
        self.media_player = None

    def start(self):
        while True:
            try:
                data = self.socket.recv(1024)
                if data.startswith(PLAY_SIGNAL):
                    music_file = data[len(PLAY_SIGNAL):].decode("utf-8")
                    self.play(music_file)
                if data.startswith(STOP_SIGNAL):
                    self.stop()
            except Exception as msg:
                print("An error occured: {}".format(msg))

    def play(self, music_file):
        print("Playing {}".format(music_file))
        self.media_player = vlc.MediaPlayer(music_file)
        self.media_player.play()

    def stop(self):
        if self.media_player is not None:
            self.media_player.stop()
        else:
            print("No music currently playing!")


if __name__ == "__main__":
    c = Client("localhost", 12345)
    c.start()