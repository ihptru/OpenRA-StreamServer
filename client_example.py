#!/usr/bin/env python3

import socket

network = socket.socket ( socket.AF_INET, socket.SOCK_STREAM )

network.connect(("localhost",  33322))
try:
    while True:
        data = network.recv(1024)
        print (data.decode())
except:
    network.close()
