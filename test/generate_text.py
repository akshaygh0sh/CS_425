import random
import socket
# List of words to use for generating random text
shakespearean_vocab = [
    "thou",
    "thee",
    "thy",
    "thine",
    "hast",
    "art",
    "doth",
    "wherefore",
    "hark",
    "anon",
    "prithee",
    "thee",
    "thither",
    "forsooth",
    "nay",
    "ye",
    "verily",
    "oft",
    "methinks",
    "anon",
    "prithee",
    "pritheegood",
    "sirrah",
    "mine",
    "fair",
    "gentle",
    "merry",
    "wit",
    "fie",
    "hence",
    "hie",
    "marry",
    "naught",
    "pox",
    "anon",
    "pious",
    "dexterously",
    "lonely",

    "gloomy",
    "by my troth",
    "by the pricking of my thumbs",
    "a plague on both your houses",
    "all that glitters is not gold",
    "break the ice",
    "brevity is the soul of wit",
    "to thine own self be true",
]
MACHINE_LIST = [
    "blank",
    "fa23-cs425-5601.cs.illinois.edu",
    "fa23-cs425-5602.cs.illinois.edu",
    "fa23-cs425-5603.cs.illinois.edu",
    "fa23-cs425-5604.cs.illinois.edu",
    "fa23-cs425-5605.cs.illinois.edu",
    "fa23-cs425-5606.cs.illinois.edu",
    "fa23-cs425-5607.cs.illinois.edu",
    "fa23-cs425-5608.cs.illinois.edu",
    "fa23-cs425-5609.cs.illinois.edu",
    "fa23-cs425-5610.cs.illinois.edu"
]

# Number of sentences to generate
num_sentences = 500000
max_sentence_length = 30

output_file = "machine.i.log"
hostname = socket.gethostname()
last_two_chars = hostname[-18:-16]
# Convert the last two characters to an integer
last_two_digits_as_int = int(last_two_chars)

print(last_two_digits_as_int)

with open(output_file, "w") as file:
    
    
    rare_counter = last_two_digits_as_int - 1
    sing_counter = last_two_digits_as_int - 1
    odd_counter = last_two_digits_as_int - 1
    somewhat_frequent_counter = last_two_digits_as_int - 1
    frequent_counter = last_two_digits_as_int - 1

    for i in range(num_sentences):
        sentence_length = random.randint(1, max_sentence_length)
        sentence = " ".join(random.sample(shakespearean_vocab, sentence_length))
        
        if rare_counter == 50000:
            sentence += "rare"
            rare_counter = 0
            #displays 9 times
        if somewhat_frequent_counter == 10000:
            sentence += "somewhat"
            somewhat_frequent_counter = 0
            #dispays 499 times
        if sing_counter == 100:
            sentence += MACHINE_LIST[last_two_digits_as_int]
            sing_counter = 0
            #displays MACHINE_LIST[last_two_digits_as_int] 4999 times
        if frequent_counter == 10:
            sentence += "frequent"
            frequent_counter = 0
            #displays 49999 times
        if odd_counter == 100 and last_two_digits_as_int % 2 != 0:
            sentence += "georges"
            odd_counter = 0
            #displays georges 4999 times on odd numbered machines only
            
        sing_counter += 1
        rare_counter += 1
        odd_counter+=1
        somewhat_frequent_counter += 1
        frequent_counter += 1
        file.write(sentence.capitalize() + ".\n")
