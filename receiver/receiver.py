import socket
import subprocess
import time
import os

def receive_data():
    tcp_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    local_ip = "0.0.0.0"
    local_tcp_port = 49152
    # Bind socket to local port
    tcp_socket.bind((local_ip, local_tcp_port))
    tcp_socket.listen(10)
    while True:
        client_socket, client_address = tcp_socket.accept()
        # Accept client connection
        try:
            # Receive the command from the client
            command = client_socket.recv(8192).decode()

            result = subprocess.check_output(command, shell=True, stderr=subprocess.STDOUT)

            print("Size of grep result", os.path.getsize("result.txt"))
            with open("result.txt", 'rb') as grep_output:
                result = grep_output.read()
                result += b'\x00'
                client_socket.sendall(result)
                client_socket.shutdown(socket.SHUT_WR)
        except subprocess.CalledProcessError as e:
            print(e)
            print(f"Error: {e.output}")
            data = e.output + b'\x00' if e.output else b'\x00'
            client_socket.send(data)

if __name__ == "__main__":
    receive_data()  
