#!/usr/bin/env python

import socket
import time


# this code purpose is to send an heartbeat msg every -beat_freq- seconds
# to the ground station (for now ground station == echo_server)
# if fetchSRV doesnt get a response in 2 seconds, drone should be back to his base

TCP_IP = '127.0.0.1'
TCP_PORT = 51951
BUFFER_SIZE = 1024
MESSAGE = "beat"
beat_freq = 4  # beat_freq > 2




while(1):

    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.connect((TCP_IP, TCP_PORT))
    s.settimeout(2)  # socket operation will timeout after 2secs
    time.sleep(beat_freq)
    s.send(MESSAGE)
    try:
        data = s.recv(BUFFER_SIZE)
        print "in fetchSRV2 received data:", data
    except socket.timeout:
        # drone_back_to_base()
        print("recv got timeout")
        exit(4)
    s.close()

