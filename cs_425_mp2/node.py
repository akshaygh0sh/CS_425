import threading
import socket
import datetime
import time

class Node:
    def __init__(self):
        self.ip = self.get_ip()
        self.member_list = dict()
    
    def get_ip(self):
        try:
            hostname = socket.gethostname()
            local_ip = socket.gethostbyname(hostname)
            return local_ip 
        except Exception as e:
            print("Error:", e)
    
    # Get the ID of the node (used for when attempting to join membership list)
    def get_id(self):
        current_time = str(datetime.datetime.now())
        return self.ip + "@" + current_time


if __name__ == "__main__":
    test = Node()
    print(test.get_id())

