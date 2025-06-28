from random import shuffle

ALPHABET = list('abcdefghijklmnopqrstuvwxyz')

#generate random substition dictionary
def generate_dict(permutation, direction):
    if direction == "encrypt":
        subDict = {letter : shuffled_letter for letter, shuffled_letter in zip(ALPHABET, permutation)}
    else:
        subDict = {shuffled_letter : letter for letter, shuffled_letter in zip(ALPHABET, permutation)}
    return subDict

#encrypt plaintext with key
def encrypt(plaintext, key):
    subDict = generate_dict(key, "encrypt")
    ciphertext = []
    for char in plaintext:
        if char.isalpha():
            ciphertext.append(subDict[char.lower()])
        else:
            ciphertext.append(char)
    return "".join(ciphertext)

#decrypt ciphertext with key
def decrypt(ciphertext, key):
    subDict = generate_dict(key, "decrypt")
    plaintext = []
    for char in ciphertext:
        if char.isalpha():
            plaintext.append(subDict[char.lower()])
        else:
            plaintext.append(char)
    return "".join(plaintext)


def main():
    #generate random permutation key
    key = ALPHABET[::]
    shuffle(key)
    random_key = "".join(key)
    print(f"Random key: {random_key}")
    print()

    #get phrases
    file = open("plaintext_code.txt", "r")
    phrases = file.read().strip().split('\n\n')
    #print(phrases)

    for phrase in phrases:
        ciphertext = encrypt(phrase, key)
        print(ciphertext)
        plaintext = decrypt(ciphertext, key)
        print(plaintext)
        print()

main()