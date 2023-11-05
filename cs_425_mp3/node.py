import socket
import time
import threading
import json
import sys, os
import random
import datetime
import logging
import argparse
import hashlib
import base64
import paramiko

# Define a list of host names that represent nodes in the distributed system.
# These host names are associated with specific machines in the network.
# The 'Introducer' variable points to a specific host in the system that may serve as an introducer node.

HOST_NAME_LIST = [
    'fa23-cs425-5601.cs.illinois.edu',
    'fa23-cs425-5602.cs.illinois.edu',
    'fa23-cs425-5603.cs.illinois.edu',
    'fa23-cs425-5604.cs.illinois.edu',
    'fa23-cs425-5605.cs.illinois.edu',
    'fa23-cs425-5606.cs.illinois.edu',
    'fa23-cs425-5607.cs.illinois.edu',
    'fa23-cs425-5608.cs.illinois.edu',
    'fa23-cs425-5609.cs.illinois.edu',
    'fa23-cs425-5610.cs.illinois.edu',
]
# 'Introducor' specifies the introducer node's hostname, which plays a crucial role in system coordination.
Introducor = 'fa23-cs425-5601.cs.illinois.edu'

# 'DEFAULT_PORT_NUM' defines the default port number used for communication within the system.
DEFAULT_PORT_NUM = 12360

# Configure logging for the script. This sets up a logging system that records debug information
# to the 'output.log' file, including timestamps and log levels.
logging.basicConfig(level=logging.DEBUG,
                    filename='output.log',
                    datefmt='%Y/%m/%d %H:%M:%S',
                    format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# The `Server` class represents a node in a distributed system.
class Server:
    def __init__(self,args):
        # Initialize the server with various attributes.
        self.ip, self.current_machine_ix,  = self.get_info()
        self.port = DEFAULT_PORT_NUM
        self.heartbeat = 0
        self.timejoin = int(time.time())
        self.id = f"{self.ip}:{self.port}:{self.timejoin}"
        self.addr = (self.ip, self.port)
        self.membership_list = {
                f"{ip}:{port}:{self.timejoin}": {
                "id": f"{ip}:{port}:{self.timejoin}",
                "addr": (ip, port),
                "heartbeat": 0,
                "incarnation":0,
                "status": "Alive",
                "time": time.time(), 
            }
            for ip, port in [(IP, DEFAULT_PORT_NUM) for IP in [self.ip, Introducor]]
        }
        self.file_info = {}
        self.file_list = {}
        # List to track failed members.
        self.failed_nodes = {}
        # Thresholds for various time-based criteria.
        self.failure_time_threshold = 3
        self.cleanup_time_threshold = 3
        self.suspect_time_threshold = 3
        self.protocol_period = args.protocol_period
        # Number of times to send messages.
        self.n_send = 3
        self.status = "Alive"
        # Probability of dropping a message.
        self.drop_rate = args.drop_rate
        # Incarnation number for handling suspicion.
        self.incarnation = 0
        # Thread-safe lock for synchronization.
        self.membership_lock = threading.RLock()
        self.file_list_lock = threading.Lock()
        # Flag to enable or disable message sending for leaving group and enable and disable suspicion mechanisism
        self.enable_sending = True
        self.gossipS = False

    def get_info(self):
        try:
            hostname = socket.gethostname()
            current_machine_ix = hostname[13 : 15]
            local_ip = socket.gethostbyname(hostname)
            return local_ip, int(current_machine_ix)
        except Exception as e:
            print("Error:", e)

    def print_id(self):
        # Method to print the unique ID of the server.
        with self.membership_lock:
            print(self.id)
        
    def index_to_ip(self, index):
        index = "0" + str(index) if index < 10 else str(index)
        return f"fa23-cs425-56{index}.cs.illinois.edu"

    def ls_files(self, remote_file):
        if (remote_file in self.file_list):
            for node in self.file_list[remote_file]["locations"]:
                print(self.index_to_ip(node))
        else:
            print("File not found in SDFS")
    
    def store(self):
        with self.file_list_lock:
            stored_files = []
            for key in self.file_list:
                if (self.current_machine_ix in self.file_list[key]["locations"]):
                    stored_files.append(key)
            for file in stored_files:
                print(f"{file} stored at machine {self.current_machine_ix}")

    def update_lists(self, data_list):
        # Method to update the membership list of the server with received information.
            # Iterate through the received membership list.
            
            if "membership_list" in data_list:
                with self.membership_lock:
                    data_list = data_list["membership_list"]
                    for member_id, member_info in data_list.items():
                        if member_info['heartbeat'] == 0:
                            # Skip members with heartbeat equal to 0, to clear out the initial introducor with 0 heartbeat.
                            continue
                        if member_id in self.failed_nodes:
                            # Skip members that are already in the failed members list.
                            continue

                        member_info.setdefault("status", "Alive")
                        member_info.setdefault("incarnation", 0)
                        #if the server receive the suspect message about itself, overwrite the message with great incarnation number:
                        if member_id == self.id:
                            if member_info["status"] == "Suspect":
                                if self.incarnation < member_info["incarnation"]:
                                    self.incarnation = member_info["incarnation"] + 1
                        # Check if the member is already in the MembershipList
                        if member_id in self.membership_list:
                            current_heartbeat = self.membership_list[member_id]["heartbeat"]
                            # Incarnation overwrite heartbeat
                            if member_info["incarnation"] > self.membership_list[member_id]["incarnation"]:
                                self.membership_list[member_id] = member_info
                                self.membership_list[member_id]["time"] = time.time()
                                #if suspect print out
                                if self.membership_list[member_id]["status"] == "Suspect":
                                    logger.info("[SUS]    - {}".format(member_id))
                                    log_message = f"Incaroverwrite: ID: {member_id}, Status: {self.membership_list[member_id]['status']}, Time: {self.membership_list[member_id]['time']}\n"
                                    print("log message is ", log_message)
                            # Update only if the received heartbeat is greater and both at the same incarnation
                            elif member_info["heartbeat"] > current_heartbeat and member_info["incarnation"] == self.membership_list[member_id]["incarnation"]:
                                self.membership_list[member_id] = member_info
                                self.membership_list[member_id]["time"] = time.time()
                        else:
                            # If the member is not in the MembershipList, add it
                            self.membership_list[member_id] = member_info
                            self.membership_list[member_id]["time"] = time.time()
                            # If suspect print out 
                            if self.membership_list[member_id]["status"] == "Suspect":
                                logger.info("[SUS]    - {}".format(member_id))
                                log_message = f"Newmem        : ID: {member_id}, Status: {self.membership_list[member_id]['status']}, Time: {self.membership_list[member_id]['time']}\n"
                                print("log message is ",  log_message)
                            logger.info("[JOIN]   - {}".format(member_id))
            elif "file_info" in data_list:
                
                with self.file_list_lock:
                    data_list = data_list["file_info"]
                    # Check each value in the file_info list, if the incoming hearbeat
                    # value is greater than the local heartbeat value for that file,
                    # update the local heartbeat file value and change the local locations
                    # to the incoming locations
                    # IF there aren't enough locations (which means we lost a replica),
                    # then we should just add the next available node (if we lost 3, we add 4, etc)
                    
                    for file_key in data_list:
                        print("file info datalist is", data_list)
                        print("file info is", self.file_info)
                        try:
                            if file_key not in self.file_info:
                                #print("1")
                                self.file_info[file_key] = data_list[file_key]
                                #print("2")
                            
                            elif data_list[file_key]['heartbeat'] > self.file_info[file_key]['hearbeat']: #this statment fails
                                #print("4")
                                self.file_info[file_key]['hearbeat'] = data_list[file_key]['heartbeat']
                                #print("5")
                                self.file_info[file_key]["locations"] =  data_list[file_key]["locations"]
                                #print("6")
                        except Exception as e:
                            print("Error when updating file info:", e)
                            
                

    def suspect_nodes(self):
        # Method to detect and handle suspected and failed members in the membership list for the gossip S protocol.
        with self.membership_lock:
            now = int(time.time())
            # Calculate the threshold time
            failure_threshold_time = now - self.failure_time_threshold
            suspect_threshold_time = now - self.suspect_time_threshold
            # Collect members to remove
            suspect_members_detected = [member_id for member_id, member_info in self.membership_list.items() if member_info['time'] < failure_threshold_time and member_info["status"] != "Suspect"]
            for member_id in suspect_members_detected:
                self.membership_list[member_id]["status"] = "Suspect"
                self.membership_list[member_id]["incarnation"] += 1
                self.membership_list[member_id]["time"] = now
                logger.info("[SUS]    - {}".format(member_id))
                log_message = f"Detected      : ID: {member_id}, Status: {self.membership_list[member_id]['status']}, Time: {self.membership_list[member_id]['time']}\n"
                print("log message is ", log_message)
            fail_members_detected = [member_id for member_id, member_info in self.membership_list.items() if member_info['time'] < suspect_threshold_time and member_id not in self.failed_nodes and member_info['status'] == "Suspect"]
            for member_id in fail_members_detected:
                self.failed_nodes[member_id] = now
                del self.membership_list[member_id]
                logger.info("[DELETE] - {}".format(member_id))

    def detect_failed_nodes(self):
        # Method to detect and handle failed members in the membership list for the gossip protocol.
        with self.membership_lock:
            now = int(time.time())
            # Calculate the threshold time
            threshold_time = now - self.failure_time_threshold
            # Collect members to remove
            fail_members_detected = [member_id for member_id, member_info in self.membership_list.items() if member_info['time'] < threshold_time and member_id not in self.failed_nodes]
            for member_id in fail_members_detected:
                self.failed_nodes[member_id] = now
                del self.membership_list[member_id]
                logger.info("[DELETE] - {}".format(member_id))

    def remove_failed_nodes(self):
        # Remove the members from the failMembershipList
        with self.membership_lock:
            now = int(time.time())
            threshold_time = now - self.cleanup_time_threshold
            fail_members_to_remove = [member_id for member_id, fail_time in self.failed_nodes.items() if fail_time < threshold_time]
            for member_id in fail_members_to_remove:
                del self.failed_nodes[member_id]

    def json(self):
        # Method to generate a JSON representation of the server's membership information.
        with self.membership_lock:
            if self.gossipS:
            # If using GossipS protocol, include additional information like status and incarnation.
                return {
                    m['id']:{
                        'id': m['id'],
                        'addr': m['addr'],
                        'heartbeat': m['heartbeat'] ,
                        'status': m['status'],
                        'incarnation': m['incarnation']
                    }
                    for m in self.membership_list.values()
                }, self.file_info
            else:
            # If not using GossipS protocol, include basic information like ID, address, and heartbeat.
                return {
                    m['id']:{
                        'id': m['id'],
                        'addr': m['addr'],
                        'heartbeat': m['heartbeat'] ,
                    }
                    for m in self.membership_list.values()
                }, self.file_info
    # def list_json(self):
    #     with self.membership_lock:
    #         retur
        
        
    def ip_to_machine_id(self, ip):
        ip = ip.split(':')[0]
        ip_to_machine_id = {
            "172.22.158.185" : HOST_NAME_LIST[0],
            "172.22.94.185" : HOST_NAME_LIST[1],
            "172.22.156.186" : HOST_NAME_LIST[2],
            "172.22.158.186" : HOST_NAME_LIST[3],
            "172.22.94.186" : HOST_NAME_LIST[4],
            "172.22.156.187" : HOST_NAME_LIST[5],
            "172.22.158.187" : HOST_NAME_LIST[6],
            "172.22.94.187" : HOST_NAME_LIST[7],
            "172.22.156.188" : HOST_NAME_LIST[8],
            "172.22.158.188" : HOST_NAME_LIST[9]
        }   
        return ip_to_machine_id[ip]

    def print_membership_list(self):
        # Method to print the membership list to the log file and return it as a string.
        with self.membership_lock:
            timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            log_message = f"{timestamp} ==============================================================\n"
            log_message += f" {str(self.failed_nodes)}\n"
            for member_id, member_info in self.membership_list.items():
                log_message += f"ID: {member_info['id']}, Heartbeat: {member_info['heartbeat']}, Status: {member_info['status']}, Incarnation:{member_info['incarnation']}, Time: {member_info['time']}\n"
            with open('output.log', 'a') as log_file:
                log_file.write(log_message)
            return(log_message)

    def select_gossip_targets(self):
        # Method to randomly choose members from the membership list to send messages to.
        with self.membership_lock:
            candidates = list(self.membership_list.keys())
            random.shuffle(candidates)  # Shuffle the list in-place
            return candidates[:self.n_send]
    

    def receive(self):
        """
        A server's receiver is respnsible to receive all gossip UDP message:
        :return: None
        """
        with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as s:
            s.bind(self.addr)
            while True:
                try:
                    # UDP receiver
                    data, server = s.recvfrom(4096)
                    # * if receives data
                    if data:
                        if random.random() < self.drop_rate:
                            continue
                        else:
                            msgs = json.loads(data.decode('utf-8'))
                            if ("update_request" in msgs):
                                self.handle_update_request(msgs)
                            elif ("get_request" in msgs):
                                self.handle_get_request(msgs)
                            elif ("delete_request" in msgs):
                                self.handle_delete_request(msgs)
                            elif ("get_response" in msgs):
                                self.handle_get_response(msgs)
                            else:
                                self.update_lists(msgs) 
                except Exception as e:
                    print("exception ", e)
    
    def send_file(self, target_machine, local_file_path, sdfs_file_path):
        ssh_client = paramiko.SSHClient()
        ssh_client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        ssh_client.connect(target_machine, 22, self.username, self.password)

        scp_client = ssh_client.open_sftp()
        if (os.path.isfile(local_file_path)):
            scp_client.put(local_file_path, sdfs_file_path)
        scp_client.close()
        ssh_client.close()

    def get_original_location(self, file_name):
        # Get hash for file
        hash_obj = hashlib.md5(file_name.encode())
        hash_hex = hash_obj.hexdigest()
        hash_int = int(hash_hex, 16)
        return (hash_int % 10) + 1

    # Return list of all nodes at which file is stored
    def get_file_locations(self, file_name):
        original_location = self.get_original_location(file_name)
        return [(original_location + ix) % 10 + 1 for ix in range(4)]
            
    def upload_file(self, local_file_name, sdfs_file_name):
        """
        Decide where file and replicas should be stored, then gossip
        the dictionary
        """
        with self.file_list_lock:
            file_locations = self.get_file_locations(sdfs_file_name)
            local_file_path = f"/home/{self.username}/CS_425/cs_425_mp3/{local_file_name}"
            sdfs_file_path = f"/home/{self.username}/CS_425/cs_425_mp3/files/{sdfs_file_name}"
            # Send update request to necessary nodes
            self.file_info[sdfs_file_name] = {
                    "heartbeat" : self.file_info[sdfs_file_name]['hearbeat']+1 if sdfs_file_name in self.file_info else 1,
                    "locations" : self.file_info[sdfs_file_name]['locations'] if sdfs_file_name in self.file_info else file_locations
            }  
            for node in file_locations:
                target_machine = self.index_to_ip(node)
                self.send_file(target_machine, local_file_path, sdfs_file_path)
                
            
            print(f"Put file {sdfs_file_name} on machines {file_locations}")
    
    def handle_update_request(self, update_request):
        with self.file_list_lock:
            message_content = update_request["update_request"]
            sdfs_file_name = message_content["file_name"]
            if (sdfs_file_name in self.file_list):
                # More recent version, update
                if (message_content["version"] > self.file_list[sdfs_file_name]["version"]):
                    self.file_list[sdfs_file_name]["version"] = message_content["version"]
                    self.file_list[sdfs_file_name]["contents"] = message_content["contents"]
                    self.file_list[sdfs_file_name]["locations"] = message_content["locations"]
            # First time updating
            else:
                self.file_list[sdfs_file_name] = {}
                self.file_list[sdfs_file_name]["version"] = 1
                self.file_list[sdfs_file_name]["contents"] = message_content["contents"]
                self.file_list[sdfs_file_name]["locations"] = message_content["locations"]
            print("After update request", self.file_list)  
    
    def send_delete_request(self, filename):
        file_location = self.get_file_locations(filename)
        delete_request = {
            "delete_request" : {
                "file_name" : filename,
                "from" : self.current_machine_ix
            }
        }
        with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as s:
            for location in file_location:
                s.sendto(json.dumps(delete_request).encode(), (self.index_to_ip(location), DEFAULT_PORT_NUM))
    

    def handle_delete_request(self, delete_message):
        #to do
        with self.file_list_lock:
            sdfs_file_name = delete_message["delete_request"]["file_name"]
            target_node = delete_message["delete_request"]["from"]
            delete_response = {
                "delete_response" : {
                    "file_name" : sdfs_file_name,
                    "status" : "success",
                    "from" : self.index_to_ip(self.current_machine_ix)
                }
            }
            file_path = f"/home/{self.username}/CS_425/cs_425_mp3/files/{sdfs_file_name}"
            if os.path.exists(file_path):
                try:
                    # Delete the file
                    os.remove(file_path)
                except OSError as e:
                    delete_response["delete_response"]["status"] = "failure"
            else:
                delete_response["delete_response"]["status"] = "failure"

            with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as s:
                s.sendto(json.dumps(delete_response).encode(), (self.index_to_ip(target_node), DEFAULT_PORT_NUM))

                
    def handle_delete_response(self, message):
        delete_response = message["delete_response"]
        file_name = delete_response["file_name"]
        delete_from = delete_response["from"]
        if delete_response["status"] == "success":
            print(f"DELETE request succeeded: deleted {file_name}, from {delete_from}")
        else:
            print(f"Error when attempting to deleting contents of {file_name}, from {delete_from}")

    
    def send_get_request(self, sdfs_file_name):
        file_location = self.get_file_locations(sdfs_file_name)
        get_request = {
            "get_request" : {
                "file_name" : sdfs_file_name,
                "from" : self.current_machine_ix
            }
        }
        with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as s:
            s.sendto(json.dumps(get_request).encode(), (self.index_to_ip(file_location[0]), DEFAULT_PORT_NUM))
    
    def handle_get_request(self, get_message):
        with self.file_list_lock:
            sdfs_file_name = get_message["get_request"]["file_name"]
            target_node = get_message["get_request"]["from"]
            get_response = {
                    "get_response" : {
                        "file_name" : sdfs_file_name,
                        "status" : "success"
                    }
                }
            file_path = f"/home/{self.username}/CS_425/cs_425_mp3/files/{sdfs_file_name}"
            local_dir = f"/home/{self.username}/CS_425/cs_425_mp3/{sdfs_file_name}"
            if (os.path.exists(file_path)):
                self.send_file(self.index_to_ip(target_node), file_path, local_dir)
            else:
                get_response["get_response"]["status"] = "failure"

            with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as s:
                s.sendto(json.dumps(get_response).encode(), (self.index_to_ip(target_node), DEFAULT_PORT_NUM))  
    
    def handle_get_response(self, message):
        get_response = message["get_response"]
        file_name = get_response["file_name"]
        if get_response["status"] == "success":
            print(f"GET request succeeded: received contents of {file_name}")
        else:
            print(f"Error when attempting to fetch contents of {file_name}")
    
    def print_file_info(self):
        
        
        with self.file_list_lock:
            print("the info list is ", self.file_info)
    def user_input(self):
        """
        Toggle the sending process on or off.
        :param enable_sending: True to enable sending, False to disable sending.
        """
        self.username = input("What is your username: ")
        self.password = input("What is your password: ")
        while True:
            user_input = input("Enter command: (or 'exit' to terminate): ")
            if user_input == 'join':
                self.enable_sending = True
                print("Starting to send messages.")
                self.membership_list = {
                f"{ip}:{port}:{self.timejoin}": {
                "id": f"{ip}:{port}:{self.timejoin}",
                "addr": (ip, port),
                "heartbeat": 0,
                "status": "Alive",
                "incarnation": 0,
                "time": time.time(),
                }
                for ip, port in [(IP, DEFAULT_PORT_NUM) for IP in [self.ip, Introducor]]
            }    
            elif user_input == 'leave':
                self.enable_sending = False
                print("Leaving the group.")
            elif user_input == 'enable suspicion':
                self.gossipS = True
                print("Starting gossip S.")
            elif user_input == 'disable suspicion':
                self.gossipS = False
                print("Stopping gossip S.")
            elif user_input == 'list_mem':
                print(self.print_membership_list())
            
            elif user_input == 'list_file':    
                print(self.print_file_info())
            elif user_input == 'list_self':
                self.print_id()
            elif user_input.startswith('put'):
                info = user_input.split(sep = ' ')
                self.upload_file(info[1], info[2])
            elif user_input.startswith('get'):
                info = user_input.split(sep = ' ')
                self.send_get_request(info[1])
            elif user_input.startswith('delete'):
                info = user_input.split(sep = ' ')
                self.send_delete_request(info[1])
            elif user_input.startswith('ls '):
                info = user_input.split(sep = ' ')
                self.ls_files(info[1])
            elif user_input == 'store':
                self.store()
            elif user_input.lower() == 'exit':
                break
            else:
                print("Invalid input.")

    def send(self, message = None):
        """
        A UDP sender for a node. It sends json message to random N nodes periodically
        and maintain time table for handling timeout issue.
        :return: None
        """
        with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as s:
            while True:
                try:
                    if self.enable_sending:  # Check if sending is enabled
                        self.update_heartbeat()
                        peers = self.select_gossip_targets()
                        mem_list, file_info = self.json()
                            
                        mem_list = {
                            "membership_list" : mem_list
                        }
                        file_info = {
                            "file_info" : file_info
                        }
                        for peer in peers:
                            s.sendto(json.dumps(mem_list).encode('utf-8'), tuple(self.membership_list[peer]['addr']))
                            s.sendto(json.dumps(file_info).encode('utf-8'), tuple(self.membership_list[peer]['addr']))
                    time.sleep(self.protocol_period)          
                except Exception as e:
                    print("the exception is", e)
                    
    def update_heartbeat(self):
        # Method to update the server's heartbeat and refresh its status in the membership list.
        with self.membership_lock:
            self.heartbeat += 1
            self.membership_list[self.id]["status"] = "Alive"
            self.membership_list[self.id]["heartbeat"] = self.heartbeat
            self.membership_list[self.id]["time"] = time.time()
            self.membership_list[self.id]["incarnation"] = self.incarnation
            if self.gossipS:
                self.suspect_nodes()
            else:
                self.detect_failed_nodes()
            self.remove_failed_nodes()
            self.print_membership_list()

    def run(self):
        """
        Run a server as a node in group.
        There are totally two parallel processes for a single node:
        - receiver: receive all UDP message
        - sender: send gossip message periodically

        :return: None
        """
        receiver_thread = threading.Thread(target=self.receive)
        receiver_thread.daemon = True
        receiver_thread.start()

        # Start a sender thread
        sender_thread = threading.Thread(target=self.send)
        sender_thread.daemon = True
        sender_thread.start()

        # Start a to update enable sending
        user_thread = threading.Thread(target=self.user_input)
        user_thread.daemon = True
        user_thread.start()


        receiver_thread.join()
        sender_thread.join()
        user_thread.join()

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument('-t', '--protocol-period', type=float, help='Protocol period T in seconds', default=0.25)
    parser.add_argument('-d', '--drop-rate', type=float,
                        help='The message drop rate',
                        default=0)
    args = parser.parse_args()
    
    server = Server(args)
    server.run()
