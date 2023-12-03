#!/usr/bin/env python

import sys

def reduce_function(file_path):
    word_count_dict = {}
    try:
        with open(file_path, 'r') as file:
            data = file.read()
            data = data.split("\n")
            for line in data:
                if (line != ""):
                    # Split the input into key and value
                    pair = line.strip("()")
                    pair = pair.split(", ")
                    key, value = pair[0], int(pair[1])
                    if (key in word_count_dict):
                        word_count_dict[key] += value
                    else:
                        word_count_dict[key] = value
            
        return word_count_dict
    except FileNotFoundError:
        print(f"Error: File not found: {file_path}")
        sys.exit(1)

if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: word_count_reduce.py <file_path>")
        sys.exit(1)

    file_path = sys.argv[1]
    word_count_info = reduce_function(file_path)
    for key, value in word_count_info.items():
        print(f"({key}, {value})")
