import paramiko 
import concurrent.futures
import getpass
# SSH functions 



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
def connect_ssh(hostname, username, password, access_token):
    ssh_client = paramiko.SSHClient()
    ssh_client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    try:
        
        ssh_client.connect(
            hostname=hostname,
            port= 22,
            username=username,
            password=password,
        )
        # Delete folder and then clone
        ssh_client.exec_command(f"git config --global user.email {username}@illinois.edu", get_pty=True)
        ssh_client.exec_command(f"git config --global user.name {username}", get_pty=True)
        ssh_client.exec_command("git config --global --unset https.proxy", get_pty=True)
        ssh_client.exec_command("git config --global --unset http.proxy", get_pty=True)
        git_clone_command = f"rm -rf CS_425 ; git clone https://{username}:{access_token}@gitlab.engr.illinois.edu/gdurand2/CS_425.git"
        stdin, stdout, stderr, = ssh_client.exec_command(git_clone_command, get_pty=True)
        for line in iter(stdout.readline, ""):
            print(line, end="")
        print('finished.')
        print(f"Machine: {hostname}\n{stdout.read().decode()}")
        ssh_client.close()
    except Exception as e:
        print(e)
    
    return ssh_client
        
    
def main():
    username = input("Enter your username: ")
    password = getpass.getpass("Enter your password: ")
    access_token = input("Enter your access_token: ")
    with concurrent.futures.ThreadPoolExecutor(max_workers=len(MACHINE_LIST)) as executor:

        results = [executor.submit(connect_ssh, h, username, password, access_token) for h in MACHINE_LIST]
        concurrent.futures.wait(results)
    
if __name__ == "__main__":
    main()
