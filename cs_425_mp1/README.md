# CS425_MP1

## Instructions
First clone the GitHub repository.

To start the server code (receiver/receiver.py), simply start the Python script with "python3 receiver/receiver.py".

In order to get the client code which will trigger the grep queries, you need to call the script. The script has several required arguments.
The first one is -t (which stands for target machines, which is the list of machines which you want to execute the grep query on), the next is -c (which stands for command, this is the grep command you want to run on the machines). The last optional flag is -d (which stands for demo). 

If provided, the -d flag will use the provided vm1.log, vm2.log, etc files located one directory above this repository code (i.e. the log files should show up in the output of "ls .."). 

If the -d flag is not provided, the code will run with the machine.i.log files located inside the repository (i.e. within this cs425_mp1 directory). If these files are not found, obviously the grep command will not succeed.

As an example, if I wanted to get the output of "grep -n -H "GET"" on the provided vm1.log, vm2.log, etc. files on machines 1,2,3,4,5,6,7,8,9, and 10, I would call sender.py as follows:

    python3 sender/sender.py -t 1,2,3,4,5,6,7,8,9,10 -c "grep -n -H \"GET\"" -d.
