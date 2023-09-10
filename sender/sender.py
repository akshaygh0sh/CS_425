import socket
import argparse
import time
import threading

MACHINE_LIST = [
    "blank",
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
total_matching_lines = 0
def machine_arg_parser(args):
    return [int(machine_ix) for machine_ix in args.split(',')]

def create_grep_files(machine_ix, search_pattern, print_lock, is_demo):
    global total_matching_lines
    local_ip = "localhost"
    local_udp_port = 49152
    remote_port = 49152
    # Create a TCP socket
    tcp_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    
    timeout = 5
    tcp_socket.settimeout(timeout)
    tcp_socket.setsockopt(socket.SOL_SOCKET, socket.SO_RCVBUF, 8192)
    machine = MACHINE_LIST[machine_ix]
    
    try:
        tcp_socket.connect((machine, remote_port))
        commands = []
        
        if is_demo:
            command = f"grep -n -H \"{search_pattern}\" ../vm{machine_ix}.log > result.txt"
        else:
            command = f"grep -n -H \"{search_pattern}\" machine.i.log > result.txt"

        commands.append(command)
        for command in commands:
            tcp_socket.sendall(command.encode())
            received_data = b""
            while True:
                try:
                    data = tcp_socket.recv(8192)
                    # print(data.decode(), end ="")
                    received_data += data
                    if not data or data.endswith(b'\x00'):
                        break
                except Exception as e:
                    print(f"Error while connecting to machine {machine}: {str(e)}")
                    return
            
            # Synchronize print statements
            with print_lock:
                machine_line_count = len(received_data.split(b'\n')) -1
                print("Results for machine #", machine_ix, " number of maching lines", machine_line_count )
                total_matching_lines += machine_line_count
                print(received_data.decode())
    except socket.error as e:
        print("Could not connect to: ", machine, ": ", e)
    finally:
        tcp_socket.close()
        


if __name__ == "__main__":

    parser = argparse.ArgumentParser(description='Search log files on remote machines.')

    # Add required arguments
    parser.add_argument('-t', '--target_machines', type=str, nargs='+', help='Target machine(s) to search on')
    parser.add_argument('-p', '--pattern', type=str, help='Pattern to search for in log files')
    
    parser.add_argument('-d', '--demo', type=bool, help='if Demo: true, otherwise false')

    args = parser.parse_args()
    
    target_machines = machine_arg_parser(args.target_machines[0])
    search_pattern = args.pattern
    is_demo = args.demo

    print_lock = threading.Lock()
    threads = []
    start_time = time.perf_counter()
    for machine_ix in target_machines:
        thread = threading.Thread(target=create_grep_files, args=(machine_ix, search_pattern, print_lock, is_demo))
        threads.append(thread)
        thread.start()
    
    for thread in threads:
        thread.join()
    end_time = time.perf_counter()

    execution_time = end_time - start_time
    print("Total number of matching lines", total_matching_lines)
    print(f"Fetched results for pattern '{search_pattern}' on machines {str(target_machines)} in {execution_time} seconds.")