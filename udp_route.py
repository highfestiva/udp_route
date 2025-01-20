#!/usr/bin/env python3

'''
    UDP game router for testing lag and jitter. Start a local UDP server instance, which relays all packages from
    your computer to the server. Then simply connect your client to this instance instead. The server can of
    course also be run on localhost if desired.
'''

from random import uniform
from sched import scheduler
import socket
import time
from threading import Semaphore, Thread


burst_seed = 0.5


class EternalScheduler:
    def __init__(self):
        self.sched = scheduler()
        self.sem = Semaphore(0)
        Thread(target=self.run).start()

    def run(self):
        while True:
            self.sched.run()
            self.sem.acquire()

    def enter(self, delay, action, argument=()):
        self.sched.enter(delay, 1, action, argument)
        self.sem.release()


def burst(min_steps, bad_part):
    '''
        A random function that returns True or False. Internally it maintains a value ("seed") that varies between
        0 and 1, and if that value goes above `1 - bad_part`, it will return True (i.e. a network latency burst).
        The seed value moves randomly and has to move at at least `min_steps` before moving from 0 to `1 - bad_part`.

        :param min_steps: How many steps at least are required to go from 0=totally good, to 1=totally bad.
        :param bad_part: A value between 0 (all good, returns False) and 1 (all bad, returns True) that describes
                         how large portion of the return value will be True or False in a large series.
    '''
    global burst_seed
    good_end = 1 - bad_part
    step = good_end / min_steps
    burst_seed = max(0.0, min(1.0, burst_seed + uniform(-step, +step)))
    return burst_seed > good_end


def sendto(name, sock, data, addr, delay, is_burst, onsend, onexcept):
    try:
        sock.sendto(data, addr)
        onsend(delay, is_burst)
    except Exception as ex:
        if onexcept: onexcept(prefix=f'sendto {name} error', ex=ex, data=data, addr=addr)


def runrouter(targetaddr, boundaddr, latency=0.32, jitter_type='burst', jitter=0.05, loss=1.0, onsend=None, ondrop=None, onexcept=None):
    latency, jitter = latency/2, jitter/2    # Half time there, half time home.
    targetaddr, boundaddr = [(socket.gethostbyname(addr[0]), addr[1]) for addr in [targetaddr, boundaddr]]
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)    # UDP
    sock.bind(boundaddr)
    lastclientaddr = None
    scheduler = EternalScheduler()
    while True:
        try:
            data, fromaddr = sock.recvfrom(4096)
        except Exception as ex:
            if onexcept: onexcept(prefix='recv error', ex=ex)
            continue
        if uniform(0.0, 100.0) < loss:
            if ondrop: ondrop()
            continue
        is_burst = False
        if jitter_type == 'burst':
            is_burst = burst(10, 1/5)
            delay = latency + (jitter if is_burst else 0)
        elif jitter_type == 'uniform':
            delay = latency + uniform(0.0, jitter)
        else:
            assert False, 'Unknown jitter type!'
        if fromaddr == targetaddr:
            # Server to client.
            if lastclientaddr:
                scheduler.enter(delay, sendto, ('client', sock, data, lastclientaddr, delay, is_burst, onsend, onexcept))
        else:
            # Client to server.
            lastclientaddr = fromaddr
            scheduler.enter(delay, sendto, ('server', sock, data, targetaddr, delay, is_burst, onsend, onexcept))


def main():
    import sys
    if len(sys.argv) != 6:
        print('Usage:       %s <server_ip:port> <bound_ip:port> <latency> <jitter_type>:<jitter> <loss_percent>' % sys.argv[0])
        print('Example:     %s somedomain.com:1234 0.0.0.0:54321 0.04 burst:0.1 5.4' % sys.argv[0])
        print('jitter_type: burst or uniform')
        sys.exit(1)
    targetaddr, boundaddr = [x.split(':') for x in sys.argv[1:3]]
    is_local_addr = lambda addr: 'localhost' in addr or '127.0.0.1' in addr
    if is_local_addr(boundaddr[0]) and not is_local_addr(targetaddr[0]):
        print(f'WARNING: you should probably bind to 0.0.0.0 instead of {boundaddr[0]}!')
        time.sleep(10)
    targetaddr, boundaddr = [(socket.gethostbyname(addr[0]), int(addr[1])) for addr in [targetaddr, boundaddr]]
    latency, jitter, loss = sys.argv[3:6]
    jitter_type, _, jitter = jitter.partition(':')
    latency, jitter, loss = float(latency), float(jitter), float(loss)
    def onsend(delay, is_burst):
        print('.:'[int(is_burst)], end='', flush=True)
    def ondrop():
        print('d', end='', flush=True)
    def onexcept(prefix, ex, **kwargs):
        extra = str(kwargs) if kwargs else ''
        print(f'\n{prefix}: {type(ex)} {ex} {extra}')
    print('UDP (game) router by jonas@pixeldoctrine.com.')
    print('Sending towards server: %s.' % str(targetaddr))
    print('Connect your client to: %s.' % str(boundaddr))
    print('Latency setting:        %g s' % latency)
    print('Jitter setting:         %g s (%s)' % (jitter, jitter_type))
    print('Packet loss setting:    %g%%' % loss)
    print('. means packet routed, : means packet routed with burst jitter, d means packet dropped')
    runrouter(targetaddr, boundaddr, latency, jitter_type, jitter, loss, onsend, ondrop, onexcept)


if __name__ == '__main__':
    main()
