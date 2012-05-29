#!/usr/bin/env python3

import socket
import json
network = socket.socket ( socket.AF_INET, socket.SOCK_STREAM )

network.connect(("ix.lv-vl.net",  33322))
while True:
    data = network.recv(10024)
    print(data.decode())
network.close()
