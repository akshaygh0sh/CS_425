import socket

# Define the remote device's IP address and UDP port
remote_ip = "REMOTE_DEVICE_IP_ADDRESS"
remote_port = REMOTE_DEVICE_UDP_PORT

# Create a UDP socket
udp_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

# Define the Linux command to execute
linux_command = "ls -l /"

# Send the command to the remote device
udp_socket.sendto(linux_command.encode(), (remote_ip, remote_port))

# Close the UDP socket
udp_socket.close()
import socket

# Define the remote device's IP address and UDP port
remote_ip = "REMOTE_DEVICE_IP_ADDRESS"
remote_port = 49152

# Create a UDP socket
udp_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

# Define the Linux command to execute
linux_command = "ls -l /"

# Send the command to the remote device
udp_socket.sendto(linux_command.encode(), (remote_ip, remote_port))

# Close the UDP socket
udp_socket.close()
