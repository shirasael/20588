import datetime
import os
import socket
import pygame

from common.general_packet import GeneralPacket, handle_packet
from syncalong.client.timer import wait_for_remote_time

from syncalong.common.length_socket import LengthSocket
from syncalong.common.file_sync_packet import FileSyncPacket, WHO_HAS, who_has_answer_packet, FILE_SEND
from syncalong.common.signal_packet import PLAY_SIGNAL, STOP_SIGNAL, SignalPacket, PAUSE_SIGNAL, UNPAUSE_SIGNAL


class UnknownSignalException(Exception):
    def __init__(self, signal):
        self.signal = signal

    def __str__(self):
        return self.__class__.__name__ + ": " + self.signal


class Client(object):
    """
    A client for synchronously playing music.
    The client connects to a server at a given address, and can either play/stop music or receive files to be played.
    All the clients received music files are saved in a local repository.
    The client synchronizes with a remote NTP server, in order to guarantee music will be played at the same time for
    all clients at once.
    """
    def __init__(self, server_ip, server_port, ntp_server, music_files_repo):
        """
        Initialize a new client by connecting to the server at the given address.

        :param server_ip: IP address of the server to connect to.
        :param server_port: Port of the server to connect to.
        :param ntp_server: Hostname of an NTP server to sync from.
        :param music_files_repo: Local path of a directory which will be used as the client's repository.
        """
        pygame.mixer.init()
        self.ntp_server = ntp_server
        self.music_files_repo = music_files_repo
        if not os.path.exists(self.music_files_repo):
            os.makedirs(self.music_files_repo) 
        self.socket = LengthSocket(socket.AF_INET, socket.SOCK_STREAM)
        self.socket.connect((server_ip, server_port))
        self.media_player = None

    def start(self):
        """
        Send the first message to the server and establish a connection.
        Then, accept new messages from the server.

        All messages received are expected to be of type GeneralPacket.
        """
        self.socket.send(bytes("hello", encoding="utf-8"))
        while True:
            recv_packet = GeneralPacket(self.socket.recv())
            handle_packet(recv_packet, {
                SignalPacket: self._handle_signal,
                FileSyncPacket: self._handle_file_sync
            })

    def _handle_play(self, music_file_path):
        """
        Play the file at the given path. If the file is not found, an exception is thrown.
        :param music_file_path: Local music file to be played.
        """
        print("Playing {}".format(music_file_path))
        pygame.mixer.music.load(music_file_path)
        pygame.mixer.music.play()

    def _handle_signal(self, signal_packet: SignalPacket):
        """
        Handle a packet of type SignalPacket: start / stop playing music, after waiting for the required amount of
        seconds (aligned with the NTP server's time).

        :param signal_packet: packet to be handled.
        """
        print("Got signal {}".format(signal_packet.signal))
        server_send_time = datetime.datetime.fromtimestamp(signal_packet.send_timestamp)
        delay = signal_packet.wait_seconds
        wait_for_remote_time(server_send_time, delay, self.ntp_server)

        music_ctl_handlers = {
            STOP_SIGNAL: pygame.mixer.music.stop,
            PAUSE_SIGNAL: pygame.mixer.music.pause,
            UNPAUSE_SIGNAL: pygame.mixer.music.unpause
        }
        if signal_packet.signal == PLAY_SIGNAL:
            music_file = signal_packet.music_file_name.decode('utf-8')
            local_music_file_path = os.path.join(self.music_files_repo, music_file)
            self._handle_play(local_music_file_path)
        elif signal_packet.signal in music_ctl_handlers:
            music_ctl_handlers[signal_packet]()
        else:
            raise UnknownSignalException(signal_packet.signal)

    def _handle_file_sync(self, file_sync_packet: FileSyncPacket):
        """
        Handle a packet of type FileSyncPacket: check if a required music file exists in the repository, or accept a
        file being sent.
        A file is considered as existing in the client if:
            - A file with the name in the FileSyncPacket exists in the client's repository
            - The file's length is the same as the length specified in the FileSyncPacket
        When a file is received by the client, it overrides the file with the same name in the repository, if it exists.

        :param file_sync_packet: packet to be handled.
        """
        local_path = os.path.join(self.music_files_repo, file_sync_packet.file_name.decode('utf-8'))
        if file_sync_packet.message_type == WHO_HAS:
            print("Got who has!")
            send_packet = who_has_answer_packet(local_path, file_sync_packet.file_size)
            self.socket.send(send_packet)
        elif file_sync_packet.message_type == FILE_SEND:
            file_size = file_sync_packet.file_size
            received = 0
            with open(local_path, 'wb') as local_file:
                while received < file_size:
                    read_size = 1024 if file_size - received >= 1024 else file_size - received
                    data = self.socket.recv(read_size)
                    received += len(data)
                    local_file.write(data)
