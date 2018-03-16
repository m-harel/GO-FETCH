#!/usr/bin/env python

import socket

TCP_IP = '10.0.0.1'
TCP_PORT = 5005
BUFFER_SIZE = 20

s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
s.bind((TCP_IP, TCP_PORT))
s.listen(1)
while True:
	conn, addr = s.accept()
	print "Connection address: {}".format(addr)
	while 1:
		data = conn.recv(BUFFER_SIZE)
		if not data: break
		print "received data: {}".format(data)
		conn.send(data) # echo
	conn.close()

# fetchSRV start immediately after power up
# Open a new directory for flight data in /tmp
# Waiting for ground unit connection
# Starting heartbeats
# Launch goFetch
# Connects to goFetch

