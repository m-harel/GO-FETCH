#!/usr/bin/env python

import socket
import time

# this file purpose is to help check the heartbeat functionality
# the code waiting for a msg and send it back
# enable time.sleep(3) to check timeout case

TCP_IP = '127.0.0.1'
TCP_PORT = 51951
BUFFER_SIZE = 20

s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
s.bind((TCP_IP, TCP_PORT))
s.listen(1)
while True:
    conn, addr = s.accept()
    while True:
        data = conn.recv(BUFFER_SIZE)
        if not data: break
        print "in echo server received data: {}".format(data)
        # time.sleep(3) command to check the case of timeout
        conn.send(data)  # echo

    conn.close()
exit(2);

# fetchSRV start immediately after power up
# Open a new directory for flight data in /tmp
# Waiting for ground unit connection
# Starting heartbeats
# Launch goFetch
# Connects to goFetch
