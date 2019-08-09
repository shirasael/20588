import socket
import sys
from contextlib import contextmanager
import struct

# the public network interface
HOST = socket.gethostbyname(socket.gethostname())


@contextmanager
def open_raw_socket(host=HOST, port=0):
    # Create a raw socket and bind it to the public interface
    s = socket.socket(socket.AF_INET,       # Socket family
                      socket.SOCK_RAW,      # Socket type
                      socket.IPPROTO_IP)    # Protocol
    s.bind((host, port))

    # Include IP headers
    s.setsockopt(socket.IPPROTO_IP, socket.IP_HDRINCL, 1)

    # Receive all packages (promisc)
    s.ioctl(socket.SIO_RCVALL, socket.RCVALL_ON)

    yield s

    # Disabled promiscuous mode
    s.ioctl(socket.SIO_RCVALL, socket.RCVALL_OFF)


def checksum_func(data):
    checksum = 0
    data_len = len(data)
    if data_len % 2:
        data_len += 1
        data += struct.pack('!B', 0)

    for i in range(0, data_len, 2):
        w = (data[i] << 8) + (data[i + 1])
        checksum += w

    checksum = (checksum >> 16) + (checksum & 0xFFFF)
    checksum = ~checksum & 0xFFFF
    return checksum


def ip2int(ip_addr):
    if ip_addr == 'localhost':
        ip_addr = '127.0.0.1'
    return [int(x) for x in ip_addr.split('.')]


def build_daatgram_to_send(data, src, dst):
    src_ip, dest_ip = ip2int(HOST), ip2int(dst[0])
    src_ip = struct.pack('!4B', *src_ip)
    dest_ip = struct.pack('!4B', *dest_ip)

    # Check the type of data
    try:
        data = data.encode()
    except AttributeError:
        pass

    src_port = src[1]
    dest_port = dst[1]

    data_len = len(data)

    udp_length = 8 + data_len

    pseudo_header = struct.pack('!BBH', 0, socket.IPPROTO_UDP, udp_length)
    pseudo_header = src_ip + dest_ip + pseudo_header
    udp_header = struct.pack('!4H', src_port, dest_port, udp_length, 0)
    checksum = checksum_func(pseudo_header + udp_header + data)
    udp_header = struct.pack('!4H', src_port, dest_port, udp_length, checksum)
    return udp_header + data


def raw_send(data, dst):
    port = 12345
    send_data = build_daatgram_to_send(data, (HOST, port), dst)
    with open_raw_socket(HOST, port) as conn:
        conn.sendto(send_data, dst)


def raw_recv():
    with open_raw_socket() as conn:
        return conn.recvfrom(65565)


def main():
    USAGE = "Usage: \n\tpython raw.py send <data> <dst_host> <dst_port>\nOr\n\tpython raw.py recv"
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
        raw_send(sys.argv[2], (sys.argv[3], int(sys.argv[4])))
        print("Sent!")
    else:
        print(USAGE)


if __name__ == "__main__":
    main()
