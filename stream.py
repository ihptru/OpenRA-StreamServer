#!/usr/bin/env python3

import urllib.request
import json
import time
import threading
import socket

class Pinger:
    def __init__(self):
        self.data_json = []
        self.stop_thread = [0]
        self.lock = [0]

    def pinger(self):
        url = 'http://master.open-ra.org/list_json.php'
        while self.stop_thread == [0]:
            time.sleep(8)
            self.lock.pop(0)
            self.lock.append(1)
            try:
                data = urllib.request.urlopen(url).read().decode()  #ping master server and fetch data
                y = json.loads(data)    #json object
                #clear
                for i in range(len(self.data_json)):
                    self.data_json.pop(i)
                #update
                for game in y:
                    self.data_json.append(game)
                self.lock.pop(0)
                self.lock.append(0)
            except:
                continue                

class Client:
    def __init__(self, pinger_data, lock):
        self.games = pinger_data
        self.lock = lock

    def work_with_client(self, sock, addr):
        state = self.games[:]
        sock.send(str(state).encode())
        while True:
            while self.lock == [1]:
                pass
            current_state = self.games[:]
            if len(state) != len(current_state):
                print("len1: "+str(len(state)))
                print("len2: "+str(len(current_state)))
                state = current_state[:]
                sock.send(str(state).encode())
                print("length different")
                continue
            # if length is unchanged, then previous state must contain at least one item which is not in current state ( in case that there is a difference )
            for game in state:
                if game not in current_state:
                    state = current_state[:]
                    sock.send(str(state).encode())
                    print("found difference")
                    break

if __name__ == "__main__":
    pinger = Pinger()
    ping_thread = threading.Thread(target=pinger.pinger)
    try:
        ping_thread.start()
        
        network = socket.socket ( socket.AF_INET, socket.SOCK_STREAM )
        network.bind(("",  33321))
        while 1:
            network.listen(1)
            sock, addr = network.accept()
            client = Client(pinger.data_json, pinger.lock)
            client_thread = threading.Thread(target=client.work_with_client,  args=(sock, addr, ))
            client_thread.start()
        network.close()
    except:
        pinger.stop_thread = [1]    #stop pinger thread
        exit(1)
        
