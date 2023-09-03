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
    "by my troth",
    "by the pricking of my thumbs",
    "a plague on both your houses",
    "all that glitters is not gold",
    "break the ice",
    "brevity is the soul of wit",
    "to thine own self be true",
]

# Number of sentences to generate
num_sentences = 100000
max_sentence_length = 10

output_file = "machine.i.log"
hostname = socket.gethostname()
last_two_chars = hostname[-18:-16]
# Convert the last two characters to an integer
last_two_digits_as_int = int(last_two_chars)

# Multiply the integer by 10,000
result = last_two_digits_as_int * 10000
# Generate random sentences and write them to a file
with open(output_file, "w") as file:
    for i in range(num_sentences):
        sentence_length = random.randint(1, max_sentence_length)
        sentence = " ".join(random.sample(shakespearean_vocab, sentence_length))
        if i == result:
            non_shakespearean_text = "Im a Robot Beep Boop"
            file.write(non_shakespearean_text + "\n")
        file.write(sentence.capitalize() + ".\n")
