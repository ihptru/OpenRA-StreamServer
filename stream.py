#!/usr/bin/env python3
#
# Copyright 2012-2013 ihptru (Igor Popov)
#
# This file is part of OpenRA-StreamServer, which is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.

# Server port: 33322

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
            time.sleep(3)
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
    def __init__(self, pinger_data, lock, clients):
        self.games = pinger_data
        self.lock = lock
        self.stop_thread = [0]
        self.clients = clients

    def work_with_client(self, sock, addr):
        state = self.games[:]
        try:
            sock.send(str(state).encode())
        except:
            self.clients.remove(self)
            print("Broken connection:", addr[0]+":"+str(addr[1]), "["+str(len(self.clients))+" clients connected]")
            return
        while True:
            while self.lock == [1]:
                pass
            if self.stop_thread == [1]:
                break
            current_state = self.games[:]
            #length of current local list and a new list is different
            if len(state) != len(current_state):
                state = current_state[:]
                try:
                    sock.send(str(state).encode())
                except:
                    self.clients.remove(self)
                    print("Broken connection:", addr[0]+":"+str(addr[1]), "["+str(len(self.clients))+" clients connected]")
                    return
                continue
            # if length is unchanged, then previous state must contain at least one item which is not in current state ( in case that there is a difference )
            # or something is changed for a particular game
            for game in state:
                found = False
                break_loops = False
                for master in current_state:
                    # `address` is a unique field
                    if game["address"] == master["address"]:
                        found = True
                        keys = ['map', 'mods', 'name', 'players', 'state']
                        for key in keys:
                            if game[key] != master[key]:
                                state = current_state[:]
                                try:
                                    # found difference in one of games
                                    sock.send(str(state).encode())
                                    # get out of a tree of loops (we already sent a new state to client)
                                    break_loops = True
                                    break
                                except:
                                    self.clients.remove(self)
                                    print("Broken connection:", addr[0]+":"+str(addr[1]), "["+str(len(self.clients))+" clients connected]")
                                    return
                        if break_loops:
                            break
                if break_loops:
                    break
                # current checked local game is not found in master server list
                if not found:
                    state = current_state[:]
                    try:
                        sock.send(str(state).encode())
                        break
                    except:
                        self.clients.remove(self)
                        print("Broken connection:", addr[0]+":"+str(addr[1]), "["+str(len(self.clients))+" clients connected]")
                        clients
                        return

if __name__ == "__main__":
    print("Starting Stream Server...")
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
            client = Client(pinger.data_json, pinger.lock, clients)  #share a list of games and lock state with client (lock is required when Pinger modifies list of games)
            client_thread = threading.Thread(target=client.work_with_client,  args=(sock, addr, ))
            client_thread.start()
            clients.append(client)
            print("Connected:", addr[0]+":"+str(addr[1]), "["+str(len(clients))+" clients connected]")
    except KeyboardInterrupt as e:
        print("*** Stopping Threads... ***")
        for cl in clients:
            cl.stop_thread = [1]    #close works with clients
        pinger.stop_thread = [1]    #stop pinger thread
        network.close()
        exit(1)
    network.close()
    exit(0)
