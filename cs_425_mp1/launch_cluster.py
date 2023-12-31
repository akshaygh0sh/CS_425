import paramiko
from github import Github
import signal
import sys
import getpass

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

ssh_client = paramiko.SSHClient()
ssh_client.set_missing_host_key_policy(paramiko.AutoAddPolicy())

def signal_handler(sig, frame):
    global stop_requested
    ssh_client.close()
    print("Received Ctrl+C. Stopping servers...")
    halt_clusters(selected_machines)
    stop_requested = True
    sys.exit(0)
    
signal.signal(signal.SIGINT, signal_handler)

# Shutdown servers on each remote machine
def halt_clusters(to_connect):
    for hostname in to_connect:
        try:
            
            ssh_client.connect(
                hostname=hostname,
                port=22,
                username=username,
                password=password,
            )

            ssh_client.exec_command("pkill -f 'python3 ./receiver/receiver.py'")
            ssh_client.close()

            print(f"Stopped TCP receiver on {hostname}")

        except Exception as e:
            print(f"Failed to connect to {hostname}: {e}")

# Launch servers on each remote machine
def launch_cluster(to_connect):
    for machine_ix in to_connect:
        hostname = machine_ix
        try:
            ssh_client.connect(
                hostname=hostname,
                port= 22,
                username=username,
                password=password,
            )
           
            
            ssh_client.exec_command("cd CS_425/cs_425_mp1 ; python3 ./receiver/receiver.py &")
            print(f"Launched TCP receiver on {hostname}")
            
            
        except Exception as e:
            print(e)


def main():
    global username
    username = input("Enter your username: ")
    global password 
    password = getpass.getpass("Enter your password: ")
    
    machines_indexs = (input("Enter machines: ").split())
    machines_indexs = [int(x) for x in machines_indexs]
    global selected_machines
    selected_machines = [MACHINE_LIST[i-1] for i in machines_indexs]
    launch_cluster(selected_machines)
    
    stop_requested = False
    try:
        while not stop_requested:
            pass
    except KeyboardInterrupt:
        pass

if __name__ == "__main__":
    main()
