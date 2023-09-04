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
    command = input("Enter your command: ")
    access_token = input("Enter your access_token: ")
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
            ssh_client.exec_command(f"git config --global user.email {username}@illinois.edu", get_pty=True)
            ssh_client.exec_command(f"git config --global user.name {username}", get_pty=True)
            ssh_client.exec_command("git config --global --unset https.proxy", get_pty=True)
            ssh_client.exec_command("git config --global --unset http.proxy", get_pty=True)
            git_clone_command = f"cd cs425_mp1 ; git {command} https://{username}:{access_token}@gitlab.engr.illinois.edu/gdurand2/cs425_mp1"
            stdin, stdout, stderr, = ssh_client.exec_command(git_clone_command, get_pty=True)
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