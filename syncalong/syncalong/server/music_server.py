import socket
import threading
from typing import List
from datetime import datetime

from syncalong.common.general_packet import GeneralPacket
from syncalong.common.length_socket import LengthSocket, send_to_all
from syncalong.common.signal_packet import *
from syncalong.common.file_sync_packet import *


class RecvClientsThread(threading.Thread):
    """
    A thread used by the music server to accept clients asynchronously.
    """
    def __init__(self, listening_socket, on_recv_callback):
        """
        Initialize the receive thread, with the given socket and the goven callback function.
        The callback will be triggered for every clients that established a new connection with the server.

        :param listening_socket: The socket to accept clients to. Must be bound and in listening mode.
        :param on_recv_callback: Function that receives data, connection and address to be called with every
                                 connection that is established.
        """
        super().__init__()
        self.listening_socket = listening_socket
        self.on_recv_callback = on_recv_callback
        self.should_stop = threading.Event()

    def run(self):
        """
        Accept a new client and call the callback, endlessly, or until `stop` is called.
        Note that there is no timeout for accepting clients.
        """
        while not self.should_stop.is_set():
            try:
                conn, address = self.listening_socket.accept()
                data = conn.recv(len('hello'))
                self.on_recv_callback(data, conn, address)
            except (Exception, OSError) as e:
                if e.errno == 10038:
                    break
                raise
            except (Exception, socket.error) as e:
                print(f"An error occured on server thread: {e}")
                raise


class MusicServer(object):
    """
    The music server is used for accepting clients (to play the music), serving them files and signaling them when to
    play music or stop playing.
    """
    clients: List[LengthSocket]

    def __init__(self, ip, port, max_clients=10):
        """
        Initialize a new server, who'll accept clients in the given ip:port.
        :param ip: The address of the server.
        :param port: The port of the server.
        :param max_clients: Maximum amount of clients to be handled by the server. Default is 10.
        """
        self.clients = []
        self.server_socket = LengthSocket(socket.AF_INET, socket.SOCK_STREAM)
        self.server_socket.bind((ip, port))
        self.server_socket.listen(max_clients)
        print(f"Accepting clients at {ip}:{port}")
        self.recv_thread = RecvClientsThread(self.server_socket,
                                             lambda data, conn, addr: self.clients.append(conn))

    def close(self):
        self.stop()
        self.server_socket.close()
        print('music server closed')
        return None

    def start(self):
        """
        Run the server and start accepting clients.
        """
        if not self.recv_thread.is_alive():
            self.recv_thread.start()

    def signal_play_all(self, music_file):
        """
        Send all the clients a signal to begin playing the given file.
        Note that this method doesn't assure that all clients actually have the needed file.

        Clients will start playing after receiving the signal and waiting some amount of time synchronized with an
        NTP server, so that all clients will play together. Waiting threshold is sent with the signal packet.

        :param music_file: Music file name to be played by client. Could be also path.
        """
        print("Signal play")
        self._send_signal(PLAY_SIGNAL, music_file_name=os.path.basename(music_file))

    def signal_stop_all(self):
        """
        Signal all the clients to stop playing music.

        Clients will stop playing after receiving the signal and waiting some amount of time synchronized with an
        NTP server, so that all clients will stop playing together. Waiting threshold is sent with the signal packet.
        """
        print("Signal stop")
        self._send_signal(STOP_SIGNAL)

    def signal_pause_all(self):
        """
        Signal all the clients to pause playing music.

        Clients will pause playing after receiving the signal and waiting some amount of time synchronized with an
        NTP server, so that all clients will stop playing together. Waiting threshold is sent with the signal packet.
        """
        print("Signal pause")
        self._send_signal(PAUSE_SIGNAL)

    def signal_unpause_all(self):
        """
        Signal all the clients to continue playing music (after pause).

        Clients will unpause playing after receiving the signal and waiting some amount of time synchronized with an
        NTP server, so that all clients will stop playing together. Waiting threshold is sent with the signal packet.
        """
        print("Signal pause")
        self._send_signal(UNPAUSE_SIGNAL)

    def serve_music_file(self, local_file_path: str):
        """
        Serve the given music file to all the clients that don't have it in their repository.
        If a client doesn't have the file, the communication with it would be as so:

        Server                                          Client
        FileSyncPacket(message_type=WHO_HAS)    --->    look for file in repository
                                                <---    FileSyncPacket(message_type=MISSING)
        FileSyncPacket(message_type=FILE_SEND)  --->    get file name and size
        file chunk (1024 bytes)                 --->    write to repository
            .                                   --->        .
            .                                   --->        .
            .                                   --->        .
        file chunk (last)                       --->    read all file size; stop reading from stream.

        :param local_file_path: Local path to a music file to be synced with all clients.
        """
        print(f"Sending file {local_file_path}")
        missing_clients = self._query_file_existence(local_file_path)
        send_to_all(missing_clients, send_file_packets(local_file_path))

    def _query_file_existence(self, local_file_path: str) -> List[LengthSocket]:
        """
        Check which of the clients have the given file in their repository.
        Return a list of all the clients that responded with `FileSyncPacket(message_type=MISSING)` to a
        `FileSyncPacket(message_type=WHO_HAS)` packet.

        :param local_file_path: File to look for in clients.
        :return: List of all the clients that don't have the required file and should be synced.
        """
        who_has = who_has_packet(local_file_path)
        missing_clients = []
        for conn in self.clients:
            print(f"{conn} has {local_file_path}?")
            try:
                conn.send(who_has)
                ans = GeneralPacket(conn.recv())[FileSyncPacket]
                if ans.message_type == MISSING:
                    missing_clients.append(conn)
                    print(f"Sending file to {conn}")
            except (Exception, socket.error) as e:
                print(f"Could not check {conn}: {e}")
        return missing_clients

    def _send_signal(self, signal, wait_seconds=DEFAULT_WAIT_SECONDS, music_file_name=None):
        """
        Send a signal packet to all the clients. Signal might be any of the signal types allows by `SignalPacket`
        :param signal: A signal accepted by `SignalPacket` (see: signal_packet.commands).
        :param wait_seconds: Amount of seconds clients should wait before executing the command signaled in
                             order to be synced.
        :param music_file_name: Name of the file to be played. Required only for play signal.
        """
        send_time = datetime.now().timestamp()
        signal_packet = SignalPacket(signal=signal,
                                     send_timestamp=send_time,
                                     wait_seconds=wait_seconds,
                                     music_file_name=music_file_name or "")
        send_to_all(self.clients, [signal_packet])

    def stop(self):
        """
        Stop the server from accepting clients.
        """
        self.recv_thread.should_stop.set()

