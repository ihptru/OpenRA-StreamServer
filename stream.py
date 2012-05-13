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
            time.sleep(5)
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
        self.stop_thread = [0]

    def work_with_client(self, sock, addr):
        state = self.games[:]
        try:
            sock.send(str(state).encode())
        except:
            print("Broken connection:", addr[0]+":"+str(addr[1]))
            return
        while True:
            while self.lock == [1]:
                pass
            if self.stop_thread == [1]:
                break
            current_state = self.games[:]
            if len(state) != len(current_state):
                state = current_state[:]
                try:
                    sock.send(str(state).encode())
                except:
                    print("Broken connection:", addr[0]+":"+str(addr[1]))
                    return
                continue
            # if length is unchanged, then previous state must contain at least one item which is not in current state ( in case that there is a difference )
            # or something is changed for a particular game
            for game in state:
                found = False
                break_loops = False
                for master in current_state:
                    if game["id"] == master["id"]:
                        found = True
                        keys = ['map', 'mods', 'name', 'address', 'players', 'state']
                        for key in keys:
                            if game[key] != master[key]:
                                state = current_state[:]
                                try:
                                    print("found difference in one of games")
                                    sock.send(str(state).encode())
                                    break_loops = True
                                    break
                                except:
                                    print("Broken connection:", addr[0]+":"+str(addr[1]))
                                    return
                        if break_loops:
                            break
                if break_loops:
                    break
                if not found:
                    state = current_state[:]
                    try:
                        print("game not found")
                        sock.send(str(state).encode())
                        break
                    except:
                        print("Broken connection:", addr[0]+":"+str(addr[1]))
                        return

if __name__ == "__main__":
    network = socket.socket ( socket.AF_INET, socket.SOCK_STREAM )
    network.bind(("",  33322))

    pinger = Pinger()
    ping_thread = threading.Thread(target=pinger.pinger)
    clients = []    #a list of clients
    try:
        ping_thread.start() #start master server pinger
        
        while True:
            network.listen(1)
            sock, addr = network.accept()   #a new client connected
            print("Connected:", addr[0]+":"+str(addr[1]))
            client = Client(pinger.data_json, pinger.lock)  #share a list of games and lock state with client (lock is required when Pinger modifies list of games)
            client_thread = threading.Thread(target=client.work_with_client,  args=(sock, addr, ))
            client_thread.start()
            clients.append(client)
    except KeyboardInterrupt as e:
        print("*** Stopping Threads... ***")
        for cl in clients:
            cl.stop_thread = [1]    #close works with clients
        pinger.stop_thread = [1]    #stop pinger thread
        network.close()
        exit(1)
    network.close()
    exit(0)
