import socket
import subprocess

# Function that is called when sender
# requests the grep results file
def process_get_result():
    pass

def receive_data():
    udp_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    local_ip = "0.0.0.0"
    local_udp_port = 49152
    # Bind socket to local port
    udp_socket.bind((local_ip, local_udp_port))
    while True:
        # Receive in chunks of 1024 bytess
        command, sender_ip_addr = udp_socket.recvfrom(1024)
        try:
            result = subprocess.check_output(command.decode(), shell=True, stderr=subprocess.STDOUT)
        except subprocess.CalledProcessError as e:
            result = e.output
        
        # print(result)
        result = result.decode() + "EOD"
        result = result.encode()
       
        bytes_sent = 0
        chunk_size = 1024
        for i in range(0, len(result), chunk_size):
            chunk = result[i:i+chunk_size]
             # Send command output to sender
            bytes_sent += udp_socket.sendto(chunk, sender_ip_addr)
        

if __name__ == "__main__":
    receive_data()