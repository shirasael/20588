import sys
from scapy.all import *

USAGE = """Usage: tracerout.py hostname/ip <protocol>
    protocol can be one of - udp/icmp else use icmp"""

UDP_PROTO = 'udp'
ICMP_PROTO = 'icmp'
TIMEOUT = 5

VALID_PROTOCOLS = [UDP_PROTO, ICMP_PROTO]
STOP_TYPES = {UDP_PROTO:3, ICMP_PROTO:0}

def createPacket(dst, ttl, protocol=ICMP_PROTO):
    if protocol == UDP_PROTO:
        pkt = IP(dst=dst, ttl=ttl) / UDP(dport=33434)
    elif protocol == ICMP_PROTO:
        pkt = IP(dst=dst, ttl=ttl) / ICMP()
    else:
        pkt = createPacket(dst, ttl)
    return pkt

def tracert(dst, protocol):
    assert type(dst) == str
    assert type(protocol) == str

    print('Starting TraceRoute to {}'.format(dst))
    if protocol not in VALID_PROTOCOLS:
        protocol = ICMP_PROTO
    for i in range(1, 28):
        pkt = createPacket(dst, i, protocol)
        # Send the packet and get a reply
        reply = sr1(pkt, verbose=0, timeout=TIMEOUT)
        if reply is None:
            # No reply =(
            continue
        elif reply.type == STOP_TYPES[protocol]:
            # We've reached our destination
            print("Done!", reply.src)
            break
        else:
            # We're in the middle somewhere
            print("%d hops away: " % i , reply.src)

if __name__ == "__main__":
    if len(sys.argv) not in (2,3):
        print(USAGE)
        exit()

    if len(sys.argv) == 2:
        sys.argv.append('')

    tracert(sys.argv[1], sys.argv[2])