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

BUFFER_SIZE = 20_000_000
total_matching_lines = 0

def machine_arg_parser(args):
    return [int(machine_ix) for machine_ix in args.split(',')]

def create_grep_files(machine_ix, grep_command, print_lock, is_demo):
    global total_matching_lines
    remote_port = 49152
    # Create a TCP socket
    tcp_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    timeout = 5
    tcp_socket.settimeout(timeout)
    machine = MACHINE_LIST[machine_ix]
    
    try:
        tcp_socket.connect((machine, remote_port))

        file_path = f"../vm{machine_ix}.log" if is_demo else 'machine.i.log'

        commands = [
            f"{grep_command} {file_path} > result.txt"
        ]

        for command in commands:
            tcp_socket.sendall(command.encode())
            received_data = b""
            while True:
                try:
                    data = tcp_socket.recv(BUFFER_SIZE)
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
                print(f"Results for machine #{machine_ix} ({machine_line_count} matching lines):")
                total_matching_lines += machine_line_count
                print(received_data[:-1].decode())
    except socket.error as e:
        print("Could not connect to: ", machine, ": ", e)
    finally:
        tcp_socket.close()
        


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Search log files on remote machines.')

    # Add required arguments
    parser.add_argument('-t', '--target_machines', type=str, nargs='+', help='Target machine(s) to search on')
    parser.add_argument('-c', '--command', type=str, help='Grep command to be executed')
    parser.add_argument('-d', '--demo', action='store_true', help='If provided, runs grep on CS 425 vm.log files, otherwise runs with our generated log files')

    args = parser.parse_args()
    
    target_machines = machine_arg_parser(args.target_machines[0])
    grep_command = args.command
    is_demo = args.demo

    print_lock = threading.Lock()
    threads = []
    start_time = time.perf_counter()
    for machine_ix in target_machines:
        thread = threading.Thread(target=create_grep_files, args=(machine_ix, grep_command, print_lock, is_demo))
        threads.append(thread)
        thread.start()
    
    for thread in threads:
        thread.join()
    end_time = time.perf_counter()

    execution_time = end_time - start_time
    print("Total number of matching lines", total_matching_lines)
    print(f"Fetched results for pattern '{grep_command}' on machines {str(target_machines)} in {execution_time} seconds.")