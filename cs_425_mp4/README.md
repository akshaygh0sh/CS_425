# MP2

## Name
MP3 Team 63

## Description
This is the repository for MP3 by Team 63. There are two main components for MP3, failure detector(MP2) and file server(MP3).
1. Failure detector: servers would perform gossiping to communicate information of servers status (Join, Failure, Suspicion). Server would maintain local membership list.
2. Introducer: introducer always runs on VM1, and everytime a new join server need to request current membership list from the introducer.
3. File server: Handle requests (put, get, delete) and send back "ack" when jobs are finished.
4. Leader: Leader is chosen from alive file servers. It'll do task scheduling for all tasks and forward request to different servers.

## Installation
To run the file server and introducer, followings are required in the environment:
Python 3.6.8 ,other enviromental details should be same as VMs provided by the course


## Usage
For running servers, cd to the file_server/ and run
```
python3 fileserver.py
```
and the termianl would output
```
Please Enter message for SDFS:
```
Enter following args for specific operations:
1. 'put {local_filename} {sdfs_filename}': put file from local to file server
2. 'get {local_filename} {sdfs_filename}': get file from file server to local
3. 'delete {sdfs_filename}': delete file from file server
4. 'ls {sdfs_filename}': list the machines that store the file
5. 'store': list the file store on sdfs on current server
6. 'multiread {sdfs_filename} {num of server}': execute read file on serveral different machine

For running introducer, cd to the introducer and run
```
python3 introducer.py
```

## Support
For any questions of running the repo, please reach out to vfchen2@illinois.edu or jy75@illinois.edu


## Contributing (Authors)
Jen-Chieh Yang (jy75), Vincent Chen (vfchen2)