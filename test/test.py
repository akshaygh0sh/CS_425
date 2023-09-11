import pytest
import subprocess
from test_helper import parse_results
import os




def test_rare():
    # Define the command to run your script
    
    total_time = 0
    with open("test/test_results/test_rare_results", "w") as results_file:
        for i in range(25):
            command = f"python3 ./sender/sender.py -t 5,6,7,8 -c 'grep -n -H \"rare\"' > results.txt"   # Replace with the actual command

            # Run the command and capture its output
            process = subprocess.Popen(
                command,
                shell=True,  # Use shell=True to execute the command in a shell
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                universal_newlines=True  # Use universal_newlines to capture text output
            )
            
            return_code = process.wait()
            results, seconds = parse_results()
            solution = {'5': '10', '6': '10', '7': '10','8': '10'}
            total_time += seconds
            assert solution['5'] == results['5']
            assert solution['6'] == results['6']
            assert solution['7'] == results['7']
            assert solution['8'] == results['8']

            stdout, stderr = process.communicate()
            results_file.write(str(seconds) + '\n')
            for key, value in results.items():
                print(f"Key: {key}, Value: {value}")
            
        
        
    print(total_time/5)
    
def test_somewhat_frequent():
    # Define the command to run your script
    
    total_time = 0
    with open("test/test_results/test_somewhat_frequent", "w") as results_file:
        for i in range(100):
            command = f"python3 ./sender/sender.py -t 5,6,7,8 -c 'grep -n -H \"somewhat\"' > results.txt"   # Replace with the actual command

            # Run the command and capture its output
            process = subprocess.Popen(
                command,
                shell=True,  # Use shell=True to execute the command in a shell
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                universal_newlines=True  # Use universal_newlines to capture text output
            )
            
            return_code = process.wait()
            results, seconds = parse_results()
            solution = {'5': '50', '6': '50', '7': '50','8': '50'}
            total_time += seconds
            assert solution['5'] == results['5']
            assert solution['6'] == results['6']
            assert solution['7'] == results['7']
            assert solution['8'] == results['8']

            stdout, stderr = process.communicate()
            results_file.write(str(seconds) + '\n')
            for key, value in results.items():
                print(f"Key: {key}, Value: {value}")
            
def test_frequent():
    # Define the command to run your script
    
    total_time = 0
    with open("test/test_results/test_frequent", "w") as results_file:
        for i in range(100):
            command = f"python3 ./sender/sender.py -t 5,6,7,8 -c 'grep -n -H \"frequent\"' > results.txt"   # Replace with the actual command

            # Run the command and capture its output
            process = subprocess.Popen(
                command,
                shell=True,  # Use shell=True to execute the command in a shell
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                universal_newlines=True  # Use universal_newlines to capture text output
            )
            
            return_code = process.wait()
            results, seconds = parse_results()
            solution = {'5': '50000', '6': '50000', '7': '50000','8': '50000'}
            total_time += seconds
            assert solution['5'] == results['5']
            assert solution['6'] == results['6']
            assert solution['7'] == results['7']
            assert solution['8'] == results['8']

            stdout, stderr = process.communicate()
            results_file.write(str(seconds) + '\n')
            for key, value in results.items():
                print(f"Key: {key}, Value: {value}")

def test_odd_machines():
    # Define the command to run your script
    
    total_time = 0
    with open("test/test_results/test_odd_machines", "w") as results_file:
        for i in range(100):
            command = f"python3 ./sender/sender.py -t 5,6,7,8 -c 'grep -n -H \"georges\"' > results.txt"   # Replace with the actual command

            # Run the command and capture its output
            process = subprocess.Popen(
                command,
                shell=True,  # Use shell=True to execute the command in a shell
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                universal_newlines=True  # Use universal_newlines to capture text output
            )
            
            return_code = process.wait()
            results, seconds = parse_results()
            solution = {'5': '5000', '6': '0', '7': '5000','8': '0'}
            total_time += seconds
            assert solution['5'] == results['5']
            assert solution['6'] == results['6']
            assert solution['7'] == results['7']
            assert solution['8'] == results['8']

            stdout, stderr = process.communicate()
            results_file.write(str(seconds) + '\n')
            for key, value in results.items():
                print(f"Key: {key}, Value: {value}")
                            
def test_machine_6():
    # Define the command to run your script
    
    total_time = 0
    with open("test/test_results/test_machine_6", "w") as results_file:
        for i in range(100):
            command = f"python3 ./sender/sender.py -t 5,6,7,8 -c 'grep -n -H \"fa23-cs425-5606.cs.illinois.edu\"' > results.txt"   # Replace with the actual command

            # Run the command and capture its output
            process = subprocess.Popen(
                command,
                shell=True,  # Use shell=True to execute the command in a shell
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                universal_newlines=True  # Use universal_newlines to capture text output
            )
            
            return_code = process.wait()
            results, seconds = parse_results()
            solution = {'5': '0', '6': '5000', '7': '0','8': '0'}
            total_time += seconds

            stdout, stderr = process.communicate()
            results_file.write(str(seconds) + '\n')
            for key, value in results.items():
                print(f"Key: {key}, Value: {value}")   