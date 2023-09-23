import threading
import socket
import datetime
import json
import time
import random

class Node:
    MACHINE_LIST = [
        "fa23-cs425-5601.cs.illinois.edu",
        "fa23-cs425-5602.cs.illinois.edu",
        "fa23-cs425-5603.cs.illinois.edu",
        "fa23-cs425-5604.cs.illinois.edu",  
        "fa23-cs425-5605.cs.illinois.edu",
        "fa23-cs425-5606.cs.illinois.edu",
        "fa23-cs425-5607.cs.illinois.edu",
        "fa23-cs425-5608.cs.illinois.edu",
        "fa23-cs425-5609.cs.illinois.edu",
        "fa23-cs425-5610.cs.illinois.edu"
    ]

    # Set heartbeat interval to 2 seconds
    HEARBEAT_INTERVAL = 2
    T_FAIL = 2
    T_CLEANUP = 2

    def __init__(self):
        self.version_number = -1
        self.ip, self.current_machine_ix,  = self.get_info()
        self.id = self.update_id()
        self.is_active = False
        self.suspicion_enabled = False
        
        self.suspicion_lock = threading.Lock()
        self.is_active_lock = threading.Lock()
        self.member_list = dict()
        self.member_list_lock = threading.Lock()
        # Used to stop gossiping (if incoming gossip has a stale timestamp don't retransmit - figure this out later)
        self.last_gossip_timestamp = ""
        
    # Gets device info (ip and machine number)
    def get_info(self):
        try:
            hostname = socket.gethostname()
            current_machine_ix = hostname[13 : 15]
            local_ip = socket.gethostbyname(hostname)
            return local_ip, int(current_machine_ix)
        except Exception as e:
            print("Error:", e)
    
    # Update the ID of the node (used for when attempting to join membership list)
    def update_id(self):
        self.version_number += 1
        return f"{self.ip}@{self.version_number}:{self.current_machine_ix}"

    def listen(self):
        udp_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        local_ip = "0.0.0.0"
        local_udp_port = 49153

        # Bind socket to local port
        udp_socket.bind((local_ip, local_udp_port))

        while True:
            try:
                # Receive the command from the client
                data, client_address = udp_socket.recvfrom(8096)
                data = data.decode()
                data = json.loads(data)
                with self.member_list_lock:
                    print(data)
                    for machine in data:
                        # New machine, update current membership list
                        if not (machine in self.member_list):
                            local_time = int(time.time())
                            self.member_list[machine] = {
                                "heartbeat_counter" : data[machine]["heartbeat_counter"],
                                "timestamp" : local_time,
                                "suspicion" : data[machine]["suspicion"],
                                "suspect" : data[machine]["suspect"]
                            }
                            self.set_suspicion(bool(data[machine]["suspicion"]))
                        else:
                            received_heartbeat_count = data[machine]["heartbeat_counter"]
                            current_heartbeat_count = self.member_list[machine]["heartbeat_counter"]
                            # Newer heartbeat, update entry
                            if (received_heartbeat_count > current_heartbeat_count):
                                local_time = int(time.time())
                                self.member_list[machine]["heartbeat_counter"] = received_heartbeat_count
                                self.member_list[machine]["timestamp"] = local_time
                                self.member_list[machine]["suspicion"] = data[machine]["suspicion"]
                                self.member_list[machine]["suspect"] = False
                                self.set_suspicion(bool(data[machine]["suspicion"]))

            except Exception as e:
                print("Error while listening:", e)
    
    def heartbeat(self):
        while True:
            try:
                local_time = int(time.time())
                # Only send heartbeats if the node has "joined" the group
                if self.is_active:
                    if (self.id in self.member_list):
                        self.member_list[self.id]["heartbeat_counter"] += 1
                        self.member_list[self.id]["timestamp"] = local_time
                        self.member_list[self.id]["suspicion"] = self.get_suspicion()
                    
                    # Prune membership list - delete failed nodes
                    with self.member_list_lock:
                        stale_entries = []
                        for machine_id in self.member_list.keys():
                            time_diff = local_time - self.member_list[machine_id]["timestamp"]
                            # # Node has failed, remove from membership list entirely
                            
                            if (time_diff >= (self.T_FAIL + self.T_CLEANUP)):
                                stale_entries.append(machine_id)
                            elif (self.suspicion_enabled and time_diff >= self.T_FAIL):
                                self.member_list[machine_id]["suspect"] = True
                        
                        for entry in stale_entries:
                            del self.member_list[entry]

                        self.gossip(self.member_list)
                    time.sleep(self.HEARBEAT_INTERVAL)
            except Exception as e:
                print("Error while sending heartbeats:", e)

    # Triggers a gossip round (sends to N/2 random machines)
    def gossip(self, message):
        target_machines = list(self.member_list.keys()) if self.is_active else list(message.keys())
        target_machines = [int(id.split(":")[1]) for id in target_machines]
        print(target_machines)
        # Remove current machine from gossip targets
        if (self.current_machine_ix in target_machines):
            target_machines.remove(self.current_machine_ix)
        num_gossip = (len(target_machines) // 2) + 1
        if (num_gossip <= len(target_machines)):
            bandwidth_bytes_per_second = float(0.0)
            target_machines = random.sample(target_machines, num_gossip)
            # print(f"Machine #{self.current_machine_ix} gossiping to: {target_machines}")
            for machine_ix in target_machines:
                bandwidth_bytes_per_second += self.send(machine_ix, message)
            bandwidth_bytes_per_second /= len(target_machines)
            
            with open("out_going_bandwidth.txt", "a+") as file:
                file.write(f"Bandwidth: {bandwidth_bytes_per_second} bytes/second\n")

        
    # Attempts to join the membership group (via introducer on machine 1)
    def join_group(self):
        self.id = self.update_id()
        with self.is_active_lock:
            self.is_active = True
        join_dict = {
            self.id : {
                "heartbeat_counter" : 1,
                "suspicion" : False,
                "suspect": False
            }
        }
        self.send(1,join_dict)

    # Leave group, gossip that you have left
    def leave_group(self):
        # Stop sending heartbeats
        with self.is_active_lock:
            self.is_active = False
        # Reset membership list
        self.member_list = {}

    # Sends a message via UDP to machine #<machine_ix>
    def send(self, machine_ix, message):
        udp_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        machine = self.MACHINE_LIST[machine_ix - 1]
        remote_port = 49153
        bandwidth_bytes_per_second = float(0.0)
        try:
            tosend = json.dumps(message).encode()
            start_time = time.time()
        
            udp_socket.sendto(tosend, (machine, remote_port))
            
            end_time = time.time()

            message_size_bytes = len(tosend)
            time_taken = end_time - start_time
            bandwidth_bytes_per_second = message_size_bytes / time_taken
            
        except socket.error as e:
            print("Could not connect to: ", machine, ": ", e)
        finally:
            udp_socket.close()
            return bandwidth_bytes_per_second
    
    def get_membership_list(self):
        return list(self.member_list.keys()) if self.is_active else []
    
    def set_suspicion(self, is_enabled):
        with self.suspicion_lock:
            self.suspicion_enabled = is_enabled

    def get_suspicion(self):
        return bool(self.suspicion_enabled)
    
def process_input(node, command):
    if (command == "list_mem"):
        return node.get_membership_list()
    elif (command == "list_self"):
        return node.id
    # Just to test, remove later
    elif (command.startswith("send")):
        split_ix = command.find("send ")
        node.send(2, command[split_ix + 5:])
        return ""
    elif (command == "join"):
        node.join_group()
        return ""
    elif (command == "leave"):
        node.leave_group()
        return ""
    elif (command == "bandwidth"):
        print("hey")
    elif (command == "enable suspicion"):
        node.set_suspicion(True)
        return ""
    elif (command == "disable suspicion"):
        node.set_suspicion(False)
        return ""
    else:
        return "Command not recognized."
    
def prompt_user(node):
    while True:
        user_input = input("Enter command: (or 'exit' to terminate): ")
        if user_input.lower() == 'exit':
            break
        else:
            print(process_input(node, user_input))


if __name__ == "__main__":
    current_device = Node()
    # Create a thread for user input
    listen_thread = threading.Thread(target=current_device.listen, args=())
    listen_thread.daemon = True  # Set the thread as a daemon so it doesn't block program exit
    heartbeat_thread = threading.Thread(target=current_device.heartbeat, args=())
    heartbeat_thread.daemon = True
    listen_thread.start()
    heartbeat_thread.start()

    prompt_user(current_device)

