#!/usr/bin/env python3

from random import uniform
from sched import scheduler
import socket
from threading import Semaphore, Thread


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


def runrouter(targetaddr, boundaddr, latency = 0.32, jitter = 0.05, loss = 1.0, onsend = None, ondrop = None, onexcept = None):
	latency, jitter = latency/2, jitter/2	# Half time there, half time home.
	targetaddr, boundaddr = [(socket.gethostbyname(addr[0]), addr[1]) for addr in [targetaddr, boundaddr]]
	sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)	# UDP
	sock.bind(boundaddr)
	scheduler = EternalScheduler()
	while True:
		try:
			data, fromaddr = sock.recvfrom(4096)
		except Exception as e:
			if onexcept: onexcept(e)
			continue
		if uniform(0.0, 100.0) < loss:
			if ondrop: ondrop()
			continue
		else:
			if onsend: onsend()
		delay = uniform(0.0, jitter)
		if fromaddr == targetaddr:
			# Server to client.
			scheduler.enter(delay, sock.sendto, (data, lastclientaddr))
		else:
			# Client to server.
			lastclientaddr = fromaddr
			scheduler.enter(delay, sock.sendto, (data, targetaddr))


def main():
	import sys
	if len(sys.argv) != 6:
		print('Usage:   %s <target_ip:port> <bound_ip:port> <latency> <jitter> <loss_percent>' % sys.argv[0])
		print('Example: %s somedomain.com:1234 localhost:54321 0.35 0.05 5.4' % sys.argv[0])
		sys.exit(1)
	targetaddr, boundaddr = [x.split(':') for x in sys.argv[1:3]]
	targetaddr, boundaddr = [(socket.gethostbyname(addr[0]), int(addr[1])) for addr in [targetaddr, boundaddr]]
	latency, jitter, loss = [float(x) for x in sys.argv[3:6]]
	def onsend():
		print('.', end='', flush=True)
	def ondrop():
		print('d', end='', flush=True)
	def onexcept(e):
		print('\nError:', e)
	print('UDP (game) router by highfestiva@pixeldoctrine.com.')
	print('Sending towards server: %s.' % str(targetaddr))
	print('Connect your client to: %s.' % str(boundaddr))
	print('Latency setting:        %g' % latency)
	print('Jitter setting:         %g' % jitter)
	print('Packet loss setting:    %g%%' % loss)
	print('. means packet routed, d means packet dropped.')
	runrouter(targetaddr, boundaddr, latency, jitter, loss, onsend, ondrop)


if __name__ == '__main__':
	main()
