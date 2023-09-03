import socket
import argparse
import time

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

def machine_arg_parser(args):
    return [int(machine_ix) for machine_ix in args.split(',')]

def create_grep_files(machine_ix, search_pattern):
    remote_port = 49152
    # Create a UDP socket
    udp_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    commands = [
        f"grep -n -H {search_pattern} machine.i.log > result.txt"
    ]
    for command in commands:
        udp_socket.sendto(command.encode(), (MACHINE_LIST[machine_ix], remote_port))

    udp_socket.close()

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Search log files on remote machines.')

    # Add required arguments
    parser.add_argument('-H', '--hostname', type=str, help='The current host name')
    parser.add_argument('-t', '--target_machines', type=str, nargs='+', help='Target machine(s) to search on')
    parser.add_argument('-p', '--pattern', type=str, help='Pattern to search for in log files')

    args = parser.parse_args()

    hostname = args.hostname
    target_machines = machine_arg_parser(args.target_machines[0])
    search_pattern = args.pattern

    start_time = time.perf_counter()
    for machine_ix in target_machines:
        create_grep_files(machine_ix, search_pattern)
    end_time = time.perf_counter()

    execution_time = end_time - start_time
    print(f"Fetched results for pattern '{search_pattern}' on machines {str(target_machines)} in {execution_time} seconds.")