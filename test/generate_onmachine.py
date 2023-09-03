import paramiko
from github import Github

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

def git_pull_remote(to_connect):
    username = input("Enter your username: ")
    password = input("Enter your password: ")
    ssh_client = paramiko.SSHClient()
    ssh_client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    for machine_ix in to_connect:
        hostname = machine_ix
        try:
            ssh_client.connect(
                hostname=hostname,
                port= 22,
                username=username,
                password=password,
            )
 
            command = "cd cs425_mp1 && cd test && python3 generate_text.py"
            stdin, stdout, stderr, = ssh_client.exec_command(command, get_pty=True)
            for line in iter(stdout.readline, ""):
                print(line, end="")
            print('finished.')
            print(f"Machine: {hostname}\n{stdout.read().decode()}")
            ssh_client.close()
        except Exception as e:
            print(e)


def main():
    git_pull_remote(MACHINE_LIST)

if __name__ == "__main__":
    main()