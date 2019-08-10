import socket
import sys
from contextlib import contextmanager
from scapy.layers.inet import IP, UDP
from scapy.packet import Raw

HOST = socket.gethostbyname(socket.gethostname())


@contextmanager
def open_raw_socket(host=HOST, port=socket.SOCK_RAW):
    # Create a raw socket and bind it to the public interface
    s = socket.socket(socket.AF_INET,       # Socket family
                      socket.SOCK_RAW,      # Socket type
                      socket.IPPROTO_RAW)   # protocol
    s.bind((host, port))

    # Receive all packages (promisc)
    s.ioctl(socket.SIO_RCVALL, socket.RCVALL_ON)

    yield s

    # Disabled promiscuous mode
    s.ioctl(socket.SIO_RCVALL, socket.RCVALL_OFF)


def raw_send(data, dst_host, dst_port, src_host=HOST, src_port=socket.SOCK_RAW):
    send_packet = IP(src=src_host, dst=dst_host)/UDP(sport=src_port, dport=dst_port)/Raw(data)
    with open_raw_socket() as conn:
        # Remove IP headers (we are adding them ourselves)
        conn.setsockopt(socket.IPPROTO_IP, socket.IP_HDRINCL, 1)
        conn.sendto(send_packet.build(), (dst_host, dst_port))


def raw_recv():
    with open_raw_socket() as conn:
        return conn.recvfrom(65565)


def sniff():
    with open_raw_socket() as conn:
        # Include IP headers
        conn.setsockopt(socket.IPPROTO_IP, socket.IP_HDRINCL, 1)
        while True:
            raw = conn.recvfrom(65565)
            ip = IP(str(raw))
            print(ip.show())


def main():
    USAGE = """"Usage:
        python raw.py send <data> <dst_host> <dst_port>
    Or
        python raw.py recv
    Or
        python raw.py sniff"""
    if len(sys.argv) < 2:
        print(USAGE)
        return
    elif sys.argv[1].lower() == 'recv':
        print("Receiving raw packet:")
        print(raw_recv())
    elif sys.argv[1].lower() == 'send':
        if len(sys.argv) != 5:
            print(USAGE)
            return
        print("Sending {} to {}:{}".format(sys.argv[2], sys.argv[3], sys.argv[4]))
        raw_send(sys.argv[2], sys.argv[3], int(sys.argv[4]))
        print("Sent!")
    elif sys.argv[1].lower() == 'sniff':
        print("Sniffing!")
        sniff()
    else:
        print(USAGE)


if __name__ == "__main__":
    main()
