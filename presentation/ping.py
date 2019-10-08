import sys
import argparse
from scapy.all import *
from datetime import datetime
from random import randint

DEFAULT_DATA = "itai&shira rules"
COUNT = 2
TIMEOUT = 5
TTL = 86

SUM_DATA = """
Ping statistics for {dst}:
    Packets: Sent = {snt}, Received = {res}, Lost = {lost} ({lostp}% loss),
Approximate round trip times in milli-seconds:
    Minimum = {min}ms, Maximum = {max}ms, Average = {avg}ms
"""

SUM_DATA_NO_REPLY = """
Ping statistics for {dst}:
    Packets: Sent = {snt}, Received = {res}, Lost = {lost} ({lostp}% loss),
"""

class Counter:
    def __init__(self, count, infinite):
        self.count = count
        self.infinite = infinite

    def stop(self):
        if self.infinite:
            return False
        if self.count:
            self.count -= 1
            return False
        return True

class IcmpPacket:
    def __init__(self, dst, count, data , infinite, ttl):
        assert type(dst) == str
        assert type(count) == int
        assert type(data) == str
        assert type(infinite) == bool

        self.dst = dst
        self.data = data
        self.count = count
        self.infinite = infinite
        self.ttl = ttl
        self.ip_id = randint(1000, 0xffff)
        self.icmp_seq = randint(1000, 0xffff)

    def createPacket(self):
        self.ip_id += 1
        self.icmp_seq += 1
        return IP(dst=self.dst, id=self.ip_id, ttl=self.ttl) / ICMP(seq=self.icmp_seq) / self.data

    def getIpFromIpPkt(self, pkt):
        assert type(pkt) == scapy.layers.inet.IP, "getIpFromIpPkt waits for IP packet"
        ip = ''
        for i in raw(pkt)[16:20]:
            ip += str(i) + '.'
        return ip[:-1]

    def ping(self):
        res = 0
        sent = 0
        round_times = []
        counter = Counter(self.count, self.infinite)

        try:
            pkt = self.createPacket()
        except socket.gaierror:
            print("Ping request could not find host {}. Please check the name and try again.".format(self.dst))
            exit()

        print('Pinging {} with {} bytes of data:'.format(self.getIpFromIpPkt(pkt), len(self.data)))
        try:
            while not counter.stop():
                pkt = self.createPacket()
                sending_time = datetime.now().timestamp()
                # Send the packet and get a repl
                sent += 1
                reply = sr1(pkt, verbose=0, timeout=TIMEOUT)
                if reply is None:
                    if datetime.now().timestamp() - sending_time < TIMEOUT:
                        sent -= 1
                        raise KeyboardInterrupt
                    print('Request timed out.')
                elif reply.type == 0:
                    # We've reached our destination
                    time = int((reply.payload.time-sending_time)*1000)
                    print("Reply from {dst}: bytes={bytes} time={time} TTL={ttl}".format(
                     dst=self.dst,
                     bytes=len(reply.payload.payload.load),
                     time=time,
                     ttl=reply.ttl))
                    res += 1
                    round_times.append(time)
                elif reply.type == 11:
                    print("Got TTL exceeded")

        except KeyboardInterrupt:
            pass

        if round_times:
            print(SUM_DATA.format(dst=self.dst, snt=sent, res=res, lost=sent-res,
                lostp=(sent-res)/sent*100,
                min=min(round_times),
                max=max(round_times),
                avg=sum(round_times)/len(round_times)))
        else:
            print(SUM_DATA_NO_REPLY.format(dst=self.dst, snt=sent, res=res, lost=sent-res,
                lostp=(sent-res)/sent*100))


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument('host', type=str, nargs='?',
                       help='target name/ip')
    parser.add_argument('-d','--data', type=str, default=DEFAULT_DATA, required=False,
                       help='Send buffer data. default is "{}"'.format(DEFAULT_DATA))
    parser.add_argument('-n', type=int, default=COUNT, required=False, 
                       help='Number of echo requests to send. default is {}'.format(COUNT))
    parser.add_argument('-i', type=int, default=TTL, required=False, 
                       help='Time To Live. default is {}'.format(TTL))
    parser.add_argument('-t', action='store_true', required=False,
                       help='Ping the specified host until stopped. To stop - type Control-C.')

    args = parser.parse_args()

    icmp = IcmpPacket(dst=args.host, count=args.n, data=args.data, infinite=args.t, ttl=args.i)
    icmp.ping()