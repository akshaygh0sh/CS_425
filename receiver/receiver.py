import socket
import subprocess
import time
import os

def receive_data():
    tcp_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    tcp_socket.setsockopt(socket.SOL_SOCKET, socket.SO_RCVBUF, 8192)
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

            chunk_size = 8192
            bytes_sent = 0
            print("Size of grep result", os.path.getsize("result.txt"))
            with open("result.txt", 'rb') as grep_output:
                result = grep_output.read()
                result += b'\x00'
                chunk_size = 8192
                bytes_sent = 0
                print("Size of data:", len(result))
                for i in range(0, len(result), chunk_size):
                    chunk = result[i:i + chunk_size]
                    bytes_sent += client_socket.send(chunk) 
                print("Size of sent bytes:", bytes_sent)
                client_socket.shutdown(socket.SHUT_WR)
        except Exception as e:
            print(f"Error: {str(e)}")

if __name__ == "__main__":
    receive_data()  
