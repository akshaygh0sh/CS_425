#!/usr/bin/env python

import sys
import string

def map_function(file_path):
    try:
        with open(file_path, 'r') as file:
            for line in file:
                # Remove leading and trailing whitespaces and convert to lowercase
                line = line.strip().lower()
                
                # Split the line into words
                words = line.split()
                
                # Emit key-value pairs for each word
                for word in words:
                    print(f"({word}, 1)")
    except FileNotFoundError:
        print(f"Error: File not found: {file_path}")
        sys.exit(1)

if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: word_count_map.py <file_path>")
        sys.exit(1)

    file_path = sys.argv[1]
    map_function(file_path)
