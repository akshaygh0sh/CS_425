import threading
import datetime
import subprocess
import socket
import sys
import random
import json
from collections import Counter, deque, defaultdict
import os
import subprocess
import numpy as np
sys.path.insert(0, './server')
from server import FailDetector

#########hard code area
server_nums = [i for i in range(1, 11)]
host_name = 'fa23-cs425-56{}.cs.illinois.edu'
machine_2_ip = {i: 'fa23-cs425-56{}.cs.illinois.edu'.format('0'+str(i)) for i in range(1, 10)}  #host domain names of machnine 1~9
machine_2_ip[10] = 'fa23-cs425-5610.cs.illinois.edu'                                            #host domain name of machine 10
msg_format = 'utf-8'                #data encoding format of socket programming
filelocation_list = {} # sdfs_filename: [ips which have this file]
maple_queue = {}
juice_queue = {}
host_domain_name = socket.gethostname() 
machine_id = int(host_domain_name[13:15])
file_sender_port = 5007
file_receiver_port = 5008
file_leader_port = 5009
file_sockets = {}
leader_queue = list()
schedule_counter = defaultdict(lambda : [0,0,0,0]) # schedule_counter = {'sdfsfilename':[R_count, W_count, R_pre, W_pre]}
mp3_log_path = '/home/aaghosh2/MP3_log'
put_ack = defaultdict(list)
delete_ack = defaultdict(list)
#########

fail_detector = FailDetector()

class logging():
    def __init__(self):
        with open(mp3_log_path, 'w+') as fd:
            #create an empty log file
            pass
    def info(self, log):
        print("[LOGGING INFO {}]: ".format(datetime.datetime.now()), log)
    def debug(self, log):
        print("[LOGGING DEBUG {}]: ".format(datetime.datetime.now()), log)
    def error(self, log):
        _, _, exc_tb = sys.exc_info()
        print("[LOGGING ERROR {}, in line {}]: ".format(datetime.datetime.now(), exc_tb.tb_lineno), log)
    def writelog(self, log, stdout=True):
        if stdout:
            print("[LOGGING WRITE {}]: {}".format(datetime.datetime.now(), log))
        with open(mp3_log_path, 'a+') as fd:
            print("[LOGGING WRITE {}]: {}".format(datetime.datetime.now(), log), file = fd)
        #self.fd.write(log)

logger = logging()
SUCCESS = True
FAILURE = False

def send_packet(dest, http_packet, port, request_type = None):
    """
        This function sends the http_packet to the destinations
    """
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)         
        sock.connect((dest, port))
        sock.send(http_packet)
        sock.close()
        print(f"Send_Packet success from {str(host_domain_name)} to {str(dest)}")
        return True
   
    except Exception as e:
        print(f"Connection Error while {request_type} at {str(dest)}, {str(e)}")
        return False


def send(http_packet, request_type, to_leader, replica_ips=None):

    """
        This function handles sends based on different request types/number of destinations
    """
    http_packet_bytes = json.dumps(http_packet)
    http_packet_bytes = http_packet_bytes.encode(msg_format)

    if not to_leader:

        if request_type in ['put', 'delete']:
            for dest in replica_ips:
                send_packet(dest, http_packet_bytes, file_receiver_port, request_type)

        elif request_type == 'rereplicate':
            for dest in replica_ips:
                return send_packet(dest, http_packet_bytes, file_receiver_port, request_type)
        
        elif request_type in ['get', 'finish_ack']:
            # only need to fetch first one
            send_packet(replica_ips[0], http_packet_bytes, file_receiver_port, request_type)
        
        # request_type == 'update'
        elif request_type == 'update':
            for dest in dict(fail_detector.membership_list).keys():
                if dest != host_domain_name:
                    send_packet(dest, http_packet_bytes, file_receiver_port, request_type)
        else:
            print(f"REQUEST TYPE WRONG IN SEND ERROR!! {str(request_type)}")
    
    # send from user to leader
    else:
        leader_id = min(fail_detector.membership_list.keys())
        send_packet(leader_id, http_packet_bytes, file_leader_port, request_type)
    

def put_file(http_packet):
    """
        This function puts the file from local to designated sdfs servers(4 servers)
    """
    local = http_packet['local_filename']
    sdfs = http_packet['sdfs_filename']
    source = http_packet['request_source']
    print(f"From {str(source)} to {str(host_domain_name)} for {str(sdfs)}")
    
    try:
        cmd = f'scp -o StrictHostKeyChecking=no -o UserKnownHostsFile=/dev/null aaghosh2@{source}:{local} /home/aaghosh2/MP3_FILE/{sdfs}'
        result = subprocess.check_output(cmd, shell=True)
        # logger.info(f"Complete {str(http_packet)} ")
        return_packet = {}
        return_packet['task_id'] = http_packet['task_id']
        return_packet['request_type'] = 'put_ack'
        return_packet['request_source'] = http_packet['request_source']
        return_packet['sdfs_filename'] = http_packet['sdfs_filename']
        return_packet['replica_ip'] = host_domain_name
        send(return_packet, 'put_ack', True)

    except Exception as e:
        logger.error(f"Command: {cmd}, Error: {str(e)}")


def get_file(http_packet):
    """
    Server receieve get request, need to send file back to local
    Request need to have local, sdfs_file stored at {sdfs}
    """
    local = http_packet['local_filename']
    sdfs = http_packet['sdfs_filename']
    source = http_packet['request_source']
    cmd = f'scp -o StrictHostKeyChecking=no -o UserKnownHostsFile=/dev/null /home/aaghosh2/MP3_FILE/{sdfs} aaghosh2@{source}:{local}'
    try:
        result = subprocess.check_output(cmd, shell=True)
        # logger.info(f"Complete {str(http_packet)} ")
        return_packet = {}
        return_packet['task_id'] = http_packet['task_id']
        return_packet['request_type'] = 'get_ack'
        return_packet['request_source'] = http_packet['request_source']
        return_packet['sdfs_filename'] = http_packet['sdfs_filename']
        return_packet['replica_ip'] = host_domain_name
        send(return_packet, 'get_ack', True)
    except Exception as e:
        logger.error(f"Command: {cmd}, Error: {str(e)}")

def delete_file(http_packet):
    """
        This function deletes the file at current SDFS folder (4 servers executed)
    """
    sdfs = http_packet['sdfs_filename']
    cmd = f'rm /home/aaghosh2/MP3_FILE/{sdfs}'
    try:
        result = subprocess.check_output(cmd, shell=True)
        # logger.info(f"Complete {str(http_packet)} ")
        return_packet = {}
        return_packet['task_id'] = http_packet['task_id']
        return_packet['request_type'] = 'delete_ack'
        return_packet['request_source'] = http_packet['request_source']
        return_packet['sdfs_filename'] = http_packet['sdfs_filename']
        return_packet['replica_ip'] = host_domain_name
        send(return_packet, 'get_ack', True)

    except Exception as e:
        logger.error(f"Command: {cmd}, Error: {str(e)}")

def update_file(http_packet):
    """
        This function updates the file table for put/delete commands
    """
    try:
        if 'payload' in http_packet:
            new_file_location = http_packet['payload']
            filelocation_list.update(new_file_location) # {"machine1.log":[1,2,3]} -> {"machine1.log":[1,2,3], "machine2.log":[]}
            # logger.info(f"File location list update {str(new_file_location)}")
        else:
            del_sdfs = http_packet['sdfs_filename']
            del filelocation_list[del_sdfs]
            # logger.info(f"Delete {str(del_sdfs)} Success")
    except Exception as e:
        logger.error(f'Error {str(e)}')
    

def handle_request(clientsocket, ip):
    """
    These function handles are requests that are from the leader.
    """
    query = clientsocket.recv(4096)
    
    http_packet = query.decode(msg_format)
    http_packet = json.loads(http_packet)

    logger.info(f"Received Task {str(http_packet)}")
    # each of request_type might send x
    if http_packet['request_type'] == 'put':
        put_file(http_packet)
    elif http_packet['request_type'] == 'get':
        get_file(http_packet)
    elif http_packet['request_type'] == 'delete':
        delete_file(http_packet)
    elif http_packet['request_type'] == 'update':
        update_file(http_packet)
    elif http_packet['request_type'] == 'maple':
        handleMapleRequest(http_packet)
    elif http_packet['request_type'] == 'juice':
        handleJuiceRequest(http_packet)
    elif http_packet['request_type'] == 'maple_response':
        handleMapleResponse(http_packet)
    elif http_packet['request_type'] == 'juice_response':
        handleJuiceResponse(http_packet)
    elif http_packet['request_type'] == 'finish_ack':
        task_id = http_packet['task_id']
        print(f"Task {task_id} finished from all servers")

def receiver():
    logger.info("listening and dealing with requests")
    thread_pool = {}
            
    file_sockets['reciever'].listen()                 


    while True:
        '''
        listening query (accept each connection), trigger working thread per query
        '''
        clientsocket, clientip = file_sockets['reciever'].accept()     
        '''
        multithreading programming: label each thread with query's timestamp and client ip
        end_tasks: record task_id of finished threads
        thread_pool: dictionary, key: task_id, value:working thread
        '''

        task_id = str(clientip)+'_'+str(datetime.datetime.now())
        end_tasks = []
        thread_pool[task_id] = threading.Thread(target=handle_request, args=[clientsocket, clientip])
        thread_pool[task_id].start()
        '''
        multithreading programming: join finished threads. since dictionary can't be modified during iteration
        , add the finished tasks into end_tasks, then join those thread with end_tasks
        '''
        for task in thread_pool:
            if not thread_pool[task].is_alive():
                end_tasks.append(task)
        for task in end_tasks:
            thread_pool[task_id].join()
            del thread_pool[task]
            logger.info("Finish task:[{}]".format(task))

def send2Member():
    """
    This function is from the leader to prepare the http_packet to the members
    """
    global leader_queue

    while True:

        remove_task = []
        waiting_write = defaultdict(lambda: False) 
        waiting_read = defaultdict(lambda: False) 
        for i in range(len(leader_queue)):

            http_packet = leader_queue[i]

            location_packet = {}
            #schedule_counter = {'sdfsfilename':[R_count, W_count, R_pre, W_pre]} 
            #WRITE
            if http_packet['request_type'] == 'put': 
                if schedule_counter[http_packet['sdfs_filename']][0]>0 or schedule_counter[http_packet['sdfs_filename']][1]>0 \
                    or schedule_counter[http_packet['sdfs_filename']][3]>=4:
                    waiting_write[http_packet['sdfs_filename']] = True
                    continue
                else:
                    waiting_read[http_packet['sdfs_filename']] = waiting_read[http_packet['sdfs_filename']]
                    schedule_counter[http_packet['sdfs_filename']][3] = 1
                    schedule_counter[http_packet['sdfs_filename']][2] = 0
                    schedule_counter[http_packet['sdfs_filename']][1] = 1
                remove_task.append(i)

                # select to do job
                members = list(fail_detector.membership_list.keys())
                print("Members: ",members)
                members.remove(host_domain_name)

                sdfs_filename = http_packet['sdfs_filename']
                if sdfs_filename in filelocation_list:
                    replica_ips = filelocation_list[sdfs_filename]
                else:
                    if len(members) >= 4:
                        replica_ips = random.sample(members, 4)
                    else:
                        replica_ips = random.sample(members, len(members))

                print("Replica_ips ", replica_ips)
                filelocation_list[sdfs_filename] = replica_ips
                # add counter after a job is exectued
                send(http_packet, 'put', False, replica_ips)
                location_packet['task_id'] = host_domain_name + '_'+str(datetime.datetime.now())  
                location_packet['request_type'] = 'update'
                location_packet['sdfs_filename'] = sdfs_filename
                location_packet['payload'] = {sdfs_filename:replica_ips}
                send(location_packet, 'update', False)

            #READ
            elif http_packet['request_type'] == 'get':

                if schedule_counter[http_packet['sdfs_filename']][0]>1 or schedule_counter[http_packet['sdfs_filename']][1]>0 \
                    or schedule_counter[http_packet['sdfs_filename']][2]>=4:
                    waiting_read[http_packet['sdfs_filename']] = True
                    continue
                else:
                    waiting_write[http_packet['sdfs_filename']] = waiting_write[http_packet['sdfs_filename']]
                    schedule_counter[http_packet['sdfs_filename']][3] = 0
                    schedule_counter[http_packet['sdfs_filename']][2] += 1
                    schedule_counter[http_packet['sdfs_filename']][0] += 1
                remove_task.append(i)
                
                # this should be chnaged, we need to get from a server and delete all file on servers
                # should also consider the mechnism of maintaining file table
                
                sdfs_filename = http_packet['sdfs_filename']
                loc = filelocation_list[sdfs_filename]
                send(http_packet, 'get', False, loc)

            elif http_packet['request_type'] == 'delete':
                # Re-schedule Counter
                if schedule_counter[http_packet['sdfs_filename']][0]>0 or schedule_counter[http_packet['sdfs_filename']][1]>0 \
                    or schedule_counter[http_packet['sdfs_filename']][3]>=4:
                    waiting_write[http_packet['sdfs_filename']] = True
                    continue
                else:
                    waiting_read[http_packet['sdfs_filename']] = waiting_read[http_packet['sdfs_filename']]
                    schedule_counter[http_packet['sdfs_filename']][3] = 1
                    schedule_counter[http_packet['sdfs_filename']][2] = 0
                    schedule_counter[http_packet['sdfs_filename']][1] = 1
                remove_task.append(i)

                # Do Delete task here
                try:
                    sdfs_filename = http_packet['sdfs_filename']
                    send(http_packet, request_type, False, filelocation_list[sdfs_filename])
                    location_packet['task_id'] = host_domain_name + '_'+str(datetime.datetime.now())  
                    location_packet['request_type'] = 'update'
                    location_packet['sdfs_filename'] = sdfs_filename
                    send(location_packet, 'update', False)
                except Exception as e:
                    logger.error(f"Error {str(e)}")

            elif http_packet['request_type'] =='put_ack':
                global put_ack
                source = http_packet['request_source']
                sdfs_filename = http_packet['sdfs_filename']
                replica_ip = http_packet['replica_ip']
                put_ack[sdfs_filename].append(replica_ip)
                print("Checking file location list:", filelocation_list)
                check_list = set(list(fail_detector.membership_list.keys())) & set(filelocation_list[sdfs_filename])
                remove_task.append(i)
                if sorted(list(check_list)) == sorted(put_ack[sdfs_filename]) or len(put_ack[sdfs_filename])>=len(check_list): 
                    print(f"SEND FINISH ACK TO THE USER REQUEST SOURCE at {str(replica_ip)}, check_list is {str(check_list)}, put_ack is {str(sorted(put_ack[sdfs_filename]))}")
                    put_ack[sdfs_filename] = []
                    schedule_counter[sdfs_filename][1] = 0
                    ack_packet = {}
                    ack_packet['request_type'] = 'finish_ack'
                    ack_packet['task_id'] = http_packet['task_id']
                    send(ack_packet, 'finish_ack', False, [source])
                    # remove_task.append(i)
            
            elif http_packet['request_type'] =='delete_ack':
                global delete_ack
                source = http_packet['request_source']
                sdfs_filename = http_packet['sdfs_filename']
                replica_ip = http_packet['replica_ip']
                delete_ack[sdfs_filename].append(replica_ip)
                check_list = set(fail_detector.membership_list.keys()) & set(filelocation_list[sdfs_filename])
                remove_task.append(i)
                if sorted(list(check_list)) == sorted(delete_ack[sdfs_filename]) or len(delete_ack[sdfs_filename])>=len(check_list): 
                    delete_ack[sdfs_filename] = []
                    schedule_counter[sdfs_filename][1] = 0
                    # after receive all acks, delete from file location list
                    del filelocation_list[sdfs_filename]
                    ack_packet = {}
                    ack_packet['request_type'] = 'finish_ack'
                    ack_packet['task_id'] = http_packet['task_id']
                    send(ack_packet, 'finish_ack', False, [source])
                    # remove_task.append(i)
            
            elif http_packet['request_type'] =='get_ack':
                sdfs_filename = http_packet['sdfs_filename']
                source = http_packet['request_source']
                schedule_counter[sdfs_filename][0] -= 1
                ack_packet = {}
                ack_packet['request_type'] = 'finish_ack'
                ack_packet['task_id'] = http_packet['task_id']
                send(ack_packet, 'finish_ack', False, [source])
                remove_task.append(i)

            else:
               print(f"INVALID request_type {request_type}")

        # handle logic to avoid continous same operation and starvation
        for file_name, check in waiting_read.items():
            if not check:
                schedule_counter[file_name][3] = 0
        for file_name, check in waiting_write.items():
            if not check:
                schedule_counter[file_name][2] = 0

        # remove tasks that are done from job queue
        for task in remove_task[::-1]:
            del leader_queue[task]
    

def rereplicate():
    """
        This function always detects if there are failures and proceed with rereplication
    """
    while True:
        while len(fail_detector.failure_queue) > 0:
            domain_name = fail_detector.failure_queue.popleft()
            print(f"Failure occured! {str(domain_name)}")
            for sdfs_filename, ips in filelocation_list.items():
                if domain_name in ips:
                    # update filelocation_list for all
                    filelocation_list[sdfs_filename].remove(domain_name)
                    location_packet = {}
                    location_packet['task_id'] = host_domain_name + '_'+str(datetime.datetime.now())  
                    location_packet['request_type'] = 'update'
                    location_packet['sdfs_filename'] = sdfs_filename
                    
                    send_fail = True
                    while send_fail: 
                    # create one new replica
                        mb_list = set(fail_detector.membership_list)
                        replica_source = random.choice(filelocation_list[sdfs_filename])
                        dest = random.choice(list(mb_list - set(filelocation_list[sdfs_filename])))

                        # If there is enough space to put replica
                        if dest:
                            # Add new replica destinaion if availble
                            filelocation_list[sdfs_filename].append(dest)
                            http_packet = {}
                            http_packet['task_id'] = host_domain_name + '_'+str(datetime.datetime.now())  
                            http_packet['sdfs_filename'] = sdfs_filename
                            http_packet['local_filename'] = '/home/aaghosh2/MP3_FILE/' + sdfs_filename
                            http_packet['request_type'] = "put"
                            # If request_type == 'put': user input put localfilename, sdfs_filename, source == user host_domain, replica_ips == destination
                            http_packet['request_source'] = replica_source
                            send_fail = not (send(http_packet, 'rereplicate', False, [dest]))
                            if send_fail:
                                filelocation_list[sdfs_filename].remove(dest)
                        
                        else:
                            send_fail = False
                    
                    # Send the location packet in 2 cases: 1. there is new replica destination 2. No new deplica destination, just remove it.
                    location_packet['payload'] = {sdfs_filename:filelocation_list[sdfs_filename]}
                    send(location_packet, 'update', False)

def intro_new_join():
    while True:
        while len(fail_detector.filelocation_intro_queue) > 0:
            domain_name = fail_detector.filelocation_intro_queue.popleft()
            location_packet = {}
            location_packet['task_id'] = 'newjoin_' + host_domain_name + '_'+str(datetime.datetime.now())  
            location_packet['request_type'] = 'update'
            location_packet['payload'] = filelocation_list
            send(location_packet, 'update', False)

def leader_main():
    global leader_queue

    # Keep checking if self is leader
    while True:
        if len(fail_detector.membership_list.keys())>1:
            min_now = min(fail_detector.membership_list.keys())
            if min_now == host_domain_name:
                break
    
    rereplicate_thread = threading.Thread(target = rereplicate)
    rereplicate_thread.start()

    intro_new_join_thread = threading.Thread(target = intro_new_join)
    intro_new_join_thread.start()

    file_sockets['leader'].listen()
    while True:
        clientsocket, clientip = file_sockets['leader'].accept()
        query = clientsocket.recv(1024)
        http_packet = query.decode(msg_format)
        http_packet = json.loads(http_packet)
        logger.info(f"Receive {http_packet['request_type']} from {http_packet['request_source']}")
        leader_queue.append(http_packet)
    

def send2Leader(request_type, sdfs_filename, local_filename = None, host_domain_name = host_domain_name):
    """
    This function is to handle user inputs and prepare packet to send to leader.
    """

    http_packet = {}
    http_packet['task_id'] = host_domain_name + '_'+str(datetime.datetime.now())
    print(f"Task {http_packet['task_id']} starts! ")  
    http_packet['sdfs_filename'] = sdfs_filename
    http_packet['local_filename'] = local_filename
    http_packet['request_type'] = request_type
    http_packet['request_source'] = host_domain_name

    # use socket['result_port] to get result
    if request_type in ['put', 'get', 'delete', 'maple']:
        send(http_packet, request_type, True)

    else:
        print(f"INVALID request_type {request_type}")

def downloadFile (sdfs_file_name):
    if (sdfs_file_name in filelocation_list):
        file_location = random.choice(filelocation_list[sdfs_file_name])
        cmd = f'scp -o StrictHostKeyChecking=no -o UserKnownHostsFile=/dev/null aaghosh2@{file_location}:/home/aaghosh2/MP3_FILE/{sdfs_file_name} /home/aaghosh2/MP3_LOCAL/{sdfs_file_name}'
        try:
            result = subprocess.check_output(cmd, shell=True)
        except Exception as e:
            logger.error(f"init local/sdfs dir error: {str(e)}")


def sendMapleRequest(maple_exe, num_maples, intermediate_prefix, sdfs_src_dir):
    num_maples = int(num_maples)
    http_packet = {}
    http_packet['task_id'] = host_domain_name + '_' + str(datetime.datetime.now())
    http_packet['maple_exe'] = maple_exe
    http_packet['request_type'] = 'maple'
    http_packet['map_file'] = sdfs_src_dir
    http_packet['num_maples'] = num_maples
    maple_targets = []
    members = list(fail_detector.membership_list.keys())
    if len(members) >= num_maples:
        maple_targets = random.sample(members, num_maples)
    else:
        maple_targets = random.sample(members, len(members))

    # Maple ID denotes the that this worker
    # is in charge of the (maple_id - 1) * lines_per_worker to the (maple_id * lines_per_worker)
    # number of lines
    maple_queue[http_packet['task_id']] = {
        "pending_workers" : list(range(1, num_maples + 1)),
        "accumulated_results" : "",
        "prefix" : intermediate_prefix
    }
    ix = 1
    for target in maple_targets:
        http_packet['maple_id'] = ix
        ix+=1
        http_packet_bytes = json.dumps(http_packet)
        http_packet_bytes = http_packet_bytes.encode(msg_format)
        send_packet(target, http_packet_bytes, file_receiver_port, 'maple')

# Get all files in the file system that match the prefix
# and split them into num_juices # of chunks
def getAllFiles(sdfs_intermediate_prefix, num_juices):
    files = list(filelocation_list.keys())
    matching_files = [file for file in files if file.startswith(sdfs_intermediate_prefix)]
    matching_files = np.array_split(matching_files, num_juices)
    matching_files = [list(arr) for arr in matching_files]
    return matching_files

def sendJuiceRequest(juice_exe, num_juices, sdfs_intermediate_prefix, sdfs_dest_dir, delete_input):
    num_juices = int(num_juices)
    http_packet = {}
    http_packet['task_id'] = host_domain_name + '_' + str(datetime.datetime.now())
    http_packet['juice_exe'] = juice_exe
    http_packet['request_type'] = 'juice'
    http_packet['num_juices'] = num_juices
    juice_targets = []
    members = list(fail_detector.membership_list.keys())
    if len(members) >= num_juices:
        juice_targets = random.sample(members, num_juices)
    else:
        juice_targets = random.sample(members, len(members))
    
    matching_files = getAllFiles(sdfs_intermediate_prefix, num_juices)
    juice_queue[http_packet['task_id']] = {
        "pending_workers" : list(range(1, num_juices + 1)),
        "accumulated_results" : "",
        "sdfs_dest_filename" : sdfs_dest_dir,
        "delete_input" : delete_input
    }
    ix = 1
    for target in juice_targets:
        http_packet['juice_id'] = ix
        http_packet['files_to_reduce'] = matching_files[ix - 1]
        ix+=1
        http_packet_bytes = json.dumps(http_packet)
        http_packet_bytes = http_packet_bytes.encode(msg_format)
        print("Test before sending juice request")
        send_packet(target, http_packet_bytes, file_receiver_port, 'juice')
        print("Finish sending juice request")


def handleMapleRequest(http_packet):
    maple_exe = http_packet['maple_exe']
    map_file = http_packet['map_file']
    maple_id = int(http_packet['maple_id'])
    num_maples = int(http_packet['num_maples'])
    task_id =  http_packet['task_id']
    # Download file, and start processing
    downloadFile(map_file)

    with open (f"/home/aaghosh2/MP3_LOCAL/{map_file}", "r") as input_file:
        lines = input_file.readlines()
        lines_per_worker = len(lines) // num_maples
        sharded_file = f"sharded_{map_file}"
        with open (sharded_file, "w") as shard_file:
            start_index = (maple_id - 1) * lines_per_worker
            end_index = min(start_index + lines_per_worker, len(lines))
            print("Start index:", start_index, " end index:", end_index)
            shard_file.writelines(lines[start_index : end_index])

    command = [maple_exe, f"sharded_{map_file}"]
    try:
        result = subprocess.run(command, check = True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        keys_json = result.stdout.decode()
        response_packet = {}
        response_packet['request_type'] = 'maple_response'
        response_packet['maple_results'] = keys_json
        response_packet['maple_source'] = maple_id
        response_packet['task_id'] = task_id
        # Send results back to leader
        if (machine_id != "01"):
            response_packet = json.dumps(response_packet)
            response_packet = response_packet.encode(msg_format)
            send_packet('fa23-cs425-5601.cs.illinois.edu', response_packet, file_receiver_port, "maple_response")
        else:
            handleMapleResponse(response_packet)
    except Exception as e:
        logger.error(f"init local/sdfs dir error: {str(e)}")

def handleJuiceRequest(http_packet):
    juice_exe = http_packet['juice_exe']
    reduce_files = eval(http_packet['files_to_reduce'])
    juice_id = int(http_packet['juice_id'])
    num_juices = int(http_packet['num_juices'])
    task_id =  http_packet['task_id']
    # Download files, and start processing
    for file in reduce_files:
        downloadFile(file)

        command = [juice_exe, f"/home/aaghosh2/MP3_LOCAL/{file}"]
        try:
            result = subprocess.run(command, check = True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            keys_json = result.stdout.decode()
            response_packet = {}
            response_packet['request_type'] = 'juice_response'
            response_packet['juice_results'] = keys_json
            response_packet['juice_source'] = juice_id
            response_packet['task_id'] = task_id
            # Send results back to leader
            if (machine_id != "01"):
                response_packet = json.dumps(response_packet)
                response_packet = response_packet.encode(msg_format)
                send_packet('fa23-cs425-5601.cs.illinois.edu', response_packet, file_receiver_port, "juice_response")
                print("Finish handling juice request")
            else:
                handleJuiceResponse(response_packet)
                print("Finish handling juice request")
        except Exception as e:
            logger.error(f"init local/sdfs dir error: {str(e)}")

def separateKeys(data):
    data = data.split('\n')
    key_info = {}
    for line in data:
        if (line != ""):
            pair = line.strip("()")
            pair = pair.split(", ")
            key, value = pair[0], pair[1]
            if (key in key_info):
                key_info[key].append(value)
            else:
                key_info[key] = [value]
    return key_info


def handleMapleResponse(http_packet):
    maple_results = http_packet['maple_results']
    maple_source = http_packet['maple_source']
    task_id =  http_packet['task_id']
    if (task_id in maple_queue):
        if (maple_source in maple_queue[task_id]["pending_workers"]):
            maple_queue[task_id]["pending_workers"].remove(maple_source)
            maple_queue[task_id]["accumulated_results"] += maple_results
        
        # Maple phase done
        if (len(maple_queue[task_id]["pending_workers"]) == 0):
            sdfs_intermediate_prefix = maple_queue[task_id]["prefix"]
            separated_key_data = separateKeys(maple_queue[task_id]["accumulated_results"])
            for key in separated_key_data:
                intermediate_file_name = f"{sdfs_intermediate_prefix}_{key}"
                with open(f"./maple_files/{intermediate_file_name}", "w") as maple_file:
                    values = separated_key_data[key]
                    for value in values:
                        maple_file.write(f"({key}, {value})\n")
                send2Leader("put", intermediate_file_name, f"/home/aaghosh2/CS_425/cs_425_mp4/maple_files/{intermediate_file_name}")
            
            del maple_queue[task_id]
            print("All maple tasks finished.")

def handleJuiceResponse(http_packet):
    juice_results = http_packet['juice_results']
    juice_source = http_packet['juice_source']
    task_id =  http_packet['task_id']
    if (task_id in juice_queue):
        if (juice_source in juice_queue[task_id]["pending_workers"]):
            juice_queue[task_id]["pending_workers"].remove(juice_source)
            juice_queue[task_id]["accumulated_results"] += juice_results
        
        # Juice phase done
        if (len(juice_queue[task_id]["pending_workers"]) == 0):
            sdfs_dest_filename = juice_queue[task_id]["sdfs_dest_filename"]
            reduce_data = json.dumps(juice_queue[task_id]["accumulated_results"])
            with open(f"./juice_files/{sdfs_dest_filename}", "w") as juice_file:
                for key in reduce_data:
                    juice_file.write(f"({key}, {reduce_data[key]})\n")
                send2Leader("put", sdfs_dest_filename, f"/home/aaghosh2/CS_425/cs_425_mp4/juice_files/{sdfs_dest_filename}")
            
            del juice_queue[task_id]
            print("All juice tasks finished.")

def clean_local_sdfs_dir():
    try:
        # init sdfs
        cmd = 'rm -rf /home/aaghosh2/MP3_FILE'
        result = subprocess.check_output(cmd, shell=True)
        logger.info("successfully remove sdfs directory") 
        cmd = 'mkdir -p /home/aaghosh2/MP3_FILE'
        result = subprocess.check_output(cmd, shell=True)
        cmd = 'rm -rf /home/aaghosh2/CS_425/cs_425_mp4/maple_files'
        result = subprocess.check_output(cmd, shell=True)
        logger.info("successfully remove maple files directory")
        cmd = 'mkdir -p /home/aaghosh2/CS_425/cs_425_mp4/maple_files'
        result = subprocess.check_output(cmd, shell=True)
        cmd = 'rm -rf /home/aaghosh2/CS_425/cs_425_mp4/juice_files'
        result = subprocess.check_output(cmd, shell=True)
        logger.info("successfully remove juice files directory")
        cmd = 'mkdir -p /home/aaghosh2/CS_425/cs_425_mp4/juice_files'
        result = subprocess.check_output(cmd, shell=True)
        logger.info("successfully create sdfs directory")
        # init local to get files from sdfs
        cmd = 'rm -rf /home/aaghosh2/MP3_LOCAL'
        result = subprocess.check_output(cmd, shell=True)
        logger.info("successfully remove local directory")
        cmd = 'mkdir -p /home/aaghosh2/MP3_LOCAL'
        result = subprocess.check_output(cmd, shell=True)
        logger.info("successfully create local directory")
    except Exception as e:
        logger.error(f"init local/sdfs dir error: {str(e)}")
    
        
if __name__ == "__main__":

    clean_local_sdfs_dir()

    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)         
    hostip = socket.gethostname() 
    hostport = file_receiver_port               

    sock.bind((hostip, hostport))
    file_sockets['reciever'] = sock

    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)         
    hostip = socket.gethostname() 
    hostport = file_leader_port               

    sock.bind((hostip, hostport))
    file_sockets['leader'] = sock

    server_thread = threading.Thread(target=fail_detector.start_gossiping)
    server_thread.start()

    leader_thread = threading.Thread(target=leader_main)
    leader_thread.start()

    listening_thread = threading.Thread(target = receiver)
    listening_thread.start()

    leader_function_thread = threading.Thread(target=send2Member)
    leader_function_thread.start()


    while True:
        user_input = input("Please Enter message for SDFS: ")
        request_type = user_input.split(' ')[0]
        # SPECIFY LEADER TO MINIMUM ID
        try: 
            
            if request_type.lower() == "put": # host start to leave the gossiping group
                local_filename, sdfs_filename = user_input.split(' ')[1], user_input.split(' ')[2]
                send2Leader(request_type, sdfs_filename, local_filename)

            elif request_type.lower() == 'get':
                local_filename, sdfs_filename = user_input.split(' ')[2], user_input.split(' ')[1]
                send2Leader(request_type, sdfs_filename, local_filename)
            
            elif request_type.lower() == 'delete':
                sdfs_filename = user_input.split(' ')[1]
                send2Leader(request_type, sdfs_filename)

            elif request_type.lower() == 'maple':
                maple_exe, num_maples, sdfs_intermediate_prefix, sdfs_src_dir = user_input.split(' ')[1], user_input.split(' ')[2], user_input.split(' ')[3], user_input.split(' ')[4]
                sendMapleRequest(maple_exe, num_maples, sdfs_intermediate_prefix, sdfs_src_dir)

            elif request_type.lower() == 'juice':
                juice_exe, num_juices, sdfs_intermediate_prefix, sdfs_dest_dir = user_input.split(' ')[1], user_input.split(' ')[2], user_input.split(' ')[3], user_input.split(' ')[4]
                delete_input = bool(user_input.split(' ')[5])
                sendJuiceRequest(juice_exe, num_juices, sdfs_intermediate_prefix, sdfs_dest_dir, delete_input)

            elif request_type.lower() == 'ls':
                sdfs_filename = user_input.split(' ')[1]
                try:
                    print(f"Machines that store {str(sdfs_filename)} is : {str(filelocation_list[sdfs_filename])}")
                except:
                    print(f"Machines that store {str(sdfs_filename)} is : None")
            
            elif user_input.lower() == 'store':
                files = []
                for k, v in filelocation_list.items():
                    if host_domain_name in v:
                        files.append(k)
                print(f"Files store on {machine_id} is {str(files)}")
            
            elif request_type.lower() == 'multiread': # multiread sdfs_filename 2 7
                sdfs_filename, m = user_input.split(' ')[1], user_input.split(' ')[2]
                local_filename = f'/home/aaghosh2/MP3_LOCAL/{sdfs_filename}'
                mems = list(fail_detector.membership_list.keys())
                random_vms = random.sample(mems, k = int(m))
                print(f"Target VMS: {str(random_vms)}")
                for dest_domain_name in random_vms:
                    send2Leader('get', sdfs_filename, local_filename, dest_domain_name)

            elif request_type.lower() == "multiwrite": # host start to leave the gossiping group
                local_filename, sdfs_filename, m = user_input.split(' ')[1], user_input.split(' ')[2], user_input.split(' ')[3]
                mems = list(fail_detector.membership_list.keys())
                random_vms = random.sample(mems, k = int(m))
                print(f"Target VMS: {str(random_vms)}")
                for dest_domain_name in random_vms:
                    send2Leader('put', sdfs_filename, local_filename, dest_domain_name)

            elif user_input.lower() == 'filetable':
                print(f"Files table is {str(filelocation_list)}")

            ################### MP2 COMMANDS ########################
            elif user_input.lower() == "leave": # host start to leave the gossiping group
                # Terminates gossiping thread here
                leave_status = True 
                logger.info("leave start")
                for gossiping_func, gossiping_thread in dict(fail_detector.gossiping_threadpool).items():
                    logger.info(f"joining {str(gossiping_func)}")
                    gossiping_thread.join()
                    logger.info(f"finished joining {str(gossiping_func)}")
                    del fail_detector.gossiping_threadpool[gossiping_func]
                assert len(fail_detector.gossiping_threadpool) == 0
                membership_list = {}

                #clean sockets
                for sock in fail_detector.gossiping_sockets.values():
                    sock.close()
                fail_detector.gossiping_sockets = {}
                logger.info(f"Finished leaving: {host_domain_name}")

            elif user_input.lower()[:4] == "join": # host join gossiping group
                # start gossiping thread here
                msg_drop_rate = float(user_input.lower().split(' ')[-1])/100 
                logger.writelog("Joined! Msg_drop_rate {}".format(str(msg_drop_rate)))
                leave_status = False
                suspicion_mode = False
                T_fail = 4
                fail_detector.gossiping()
                fail_detector.gossiping_threadpool['plot'] = threading.Thread(target=fail_detector.plot_report)
                fail_detector.gossiping_threadpool['plot'].start()

            elif user_input.lower() == 'suspicion': # host enable suspicion mode
                fail_detector.suspicion_mode = not fail_detector.suspicion_mode
                if fail_detector.suspicion_mode:
                    fail_detector.T_fail = 2
                else:
                    fail_detector.T_fail = 4
                logger.writelog("Suspicion mode is now {}".format(str(fail_detector.suspicion_mode)))

            elif user_input.lower()[0] == 'r': # host enable message drop
                fail_detector.msg_drop_rate = float(user_input.lower().split(' ')[-1]) / 100
                logger.writelog("Message rate is now {}".format(str(fail_detector.msg_drop_rate)))

            elif user_input.lower() == 'lm': # list current membership list
                fail_detector.memberlist_lock.acquire()
                logger.info("Membership List Now: {}".format(str(fail_detector.membership_list)))
                fail_detector.memberlist_lock.release()

            elif user_input.lower() == 'm': # sorted version of 'lm'
                # logger.info("lock debug: {}".format(str(debug_lock)))
                fail_detector.memberlist_lock.acquire()
                logger.info("Membership List Now: {}".format(str(sorted(membership_list.keys()))))
                fail_detector.memberlist_lock.release()
            
            else:
                print("Invalid Argument!")
        
        except Exception as e:
            print(e)

