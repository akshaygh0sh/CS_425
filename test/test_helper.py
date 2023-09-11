import re


def parse_results():
    results = {} 
    with open('results.txt') as f:
        for line in f:
            match = re.search(r'machine \#(\d+) \((\d+) matching lines\)', line)
            if match:
                machine_num = match.group(1)
                amount_lines = match.group(2)
                
                # Store as dict with machine number as key
                results[machine_num] = amount_lines

    seconds = 0
    with open('results.txt') as f:

        for line in f:
            # Parse machine numbers and counts
            
            # Get last line
            last_line = f.readlines()[-1]

            # Use regex to extract seconds
            match = re.search(r'in (\d+\.\d+) seconds', last_line)
            if match:
                seconds = float(match.group(1))
    return results, seconds            



# results, total_seconds = parse_results('results.txt')

# print(results)
# print("Total seconds:", total_seconds)