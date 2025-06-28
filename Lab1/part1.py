import random
import math
import time
from collections import Counter

ciphers = [
    "FNCNJ LQNAB JANAJ CQNAP XXMJC VJPRL HXDTW XF",
    "NUCDM AHJVG JDHHU IEAJF JPNBE AKRJQ MHHRJ QCHRU FJBIU PHTOE KTHEA KOUPM AXEON UCPJQ PMFJM AXDUC PMKJU CBMAX AJFJP LCEHN UCDMA DUSJU CHMIE AAJPY CBHRE ZJSJ",
    "HTEBG RMAJH TMBUP PMHTJ PTMXM GPUQR JSITE DTIMB HTEBS UBHUO HTJGJ UGRJR EFEAK UAEHI JPJCA TMGGN OUPGP JHHNS CDTUO HTJHE SJSMA NBURC HEUAB IJPJB CKKJB HJXOU PHTEB GPUQR JSQCH SUBHU OHTJB JIJPJ RMPKJ RNDUA DJPAJ XIEHT HTJSU FJSJA HUOBS MRRKP JJAGE JDJBU OGMGJ PITED TIMBU XXQJD MCBJU AHTJI TURJE HIMBA HHTJB SMRRK PJJAG EJDJB UOGMG JPHTM HIJPJ CATMG GN",
    "EAHTE BTUCP EXUAU HQJRE JFJHT MHMAN XMPZA JBBIE RRJAX CPJ"
]

#preprocess to remove white space and make lowercase
for i in range(len(ciphers)):
    ciphers[i] = ciphers[i].replace(" ", "").lower()

#class to to create a pseudo dictioanry from an n-gram file with gram : frequency pairs
#this class is needed to work with memoization used in the word segmenting probability process
class GramDist(dict):
    def __init__(self, filename):
        self.gramCount = 0
        with open(filename) as file:
            for line in file:
                word, count = line.strip().split('\t')
                self[word] = int(count)
                self.gramCount += self[word]

    #if the object is called with a gram argument, calculate and return the gram's frequency
    def __call__(self, key):
        if key in self:
             return float(self[key]) / self.gramCount
        else:
            return 1.0 / (self.gramCount * 10**(len(key)-2)) #small default value for if the gram is not in the dict

#constants and frequency tables
ALPHABET = list("abcdefghijklmnopqrstuvwxyz")
bigramFreqs = GramDist("bigramFreq.txt")
trigramFreqs = GramDist("trigramFreq.txt")
singleWordFreqs = GramDist("one-grams.txt")

#load quadgrams and their frequencies, will be used to score decryptions
quadgramFreqs = {}
quadgramCount = 0
for line in open("english_quadgrams.txt", "r"):
    gram, count = line.strip().split(' ')
    quadgramFreqs[gram.lower()] = int(count)
    quadgramCount += int(count)
for key in quadgramFreqs.keys():
    quadgramFreqs[key] = math.log10(quadgramFreqs[key] / quadgramCount)

#caesars
def caesars(string, offset):
    text = []
    for char in string:
        text.append(chr(ord('a') + (ord(char) - ord('a') + offset) % 26)) #shift each character in the string
    return "".join(text)

#decrypt ciphertext with key
def decrypt(ciphertext, key):
    subDict = {shuffled_letter : letter for letter, shuffled_letter in zip(ALPHABET, key)} #map each character in alphabet to key
    plaintext = []
    #build the plaintext using the character mapping
    for char in ciphertext:
        if char.isalpha():
            plaintext.append(subDict[char.lower()])
        else:
            plaintext.append(char)
    return "".join(plaintext)

#get list of all n-grams in a message
def nGramsList(msg, n):
    nGramList = []
    l, r = 0, n #use two pointers to get the subarrays
    while r <= len(msg):
        nGramList.append(msg[l:r])
        l += 1
        r += 1
    return nGramList

#get total quadgram probability of a string
def quadGramScore(decryption):
    score = 0
    #create a list of all quadgrams in a string and iterate through them 
    for quadGram in nGramsList(decryption, 4):
        if quadGram in quadgramFreqs:
            score += quadgramFreqs[quadGram] #for every quadgram, add its frequency (probability) to total
        else:
            score += math.log10(.01 / 4224127912)   #default small value if their is no quagram frequency
    return score 

#function to get score for trigrams and bigrams that use the GramDist class
def nGramScore(decryption, n, nGramFreqs):
    score = 0
    for gram in nGramsList(decryption, n):
        score += nGramFreqs(gram)
    return score

#function to get weighted score for all different grams
def totalScore(decryption):
    score = 0
    score += nGramScore(decryption, 2, bigramFreqs) * 1
    score += nGramScore(decryption, 3, trigramFreqs) * 2
    score += quadGramScore(decryption) * 4
    return score

#get a random permutation of the alphabet
def permutation(alphabet):
    permutation = alphabet[:]
    random.shuffle(permutation)
    return permutation

#the genetic algorithms goal to continously purge and repopulate using random keys
#in hope of finding a good key to start hill clmbing with
def darwin(cipher, maxIterations=200, maxPopulation=100, survivePercent=0.67, maxNoImprove=20, mutationProb=0.1):
    """
    hyperparameters:
        maxIterations - how long the geneticAlgorithm will purge and rebuild the population
        maxPopulation - max size of each key population
        survivePercent - what percentage of the key population will survive purging
        maxNoImrove - how many times a repopulating can go on without getting a better score
        mutationProb - the chance of mutation for a key in the rebuilt population 
    """
    
    #build the initial random population of keys
    bestScore, bestKey, noImproveCount = float('-inf'), None, 0
    population = [permutation(ALPHABET) for i in range(maxPopulation)]
    
    #for a number of iterations, purge the population with the lowest decryption score and repopulate
    for iteration in range(maxIterations):
        #get all the scores of every key in the population and sort them
        scores = [(quadGramScore(decrypt(cipher, key)), key) for key in population]
        scores.sort(reverse=True, key=lambda x: x[0])

        #get a percentage of the population to survive
        survivors = []
        surviveNum = max(1, math.floor(len(population)*survivePercent))
        for i in range(surviveNum):
            survivors.append(scores[i][1])
        
        #if the topscore of the survivors is better than best overall key, update accordingly
        topKey, topScore = survivors[0], quadGramScore(decrypt(cipher, survivors[0]))
        if topScore > bestScore:
            bestScore, bestKey, noImproveCount = topScore, topKey, 0
            print(f"Current best score = {bestScore} from key = {bestKey}")
        #if not keep track that there was no improvement in the generation
        else:
            noImproveCount += 1
        
        #rebuild the population by creating child keys from the parents
        population = survivors[:]
        while len(population) < maxPopulation:
            #select two random parents and build a child key from their mappings
            p1, p2 = random.sample(survivors, 2)
            child = [random.choice([p1[i], p2[i]]) for i in range(26)]

            #get the characters the child is missing from the alphabet and the duplicate it has
            missing = [l for l in ALPHABET if l not in set(child)]
            duplicates = [l for l, c in Counter(child).items() if c > 1]

            #reaplce the duplicates with the missing chars - note theyre are an equal amount
            #this is important because for a mapping to work there must be a bijection between two alphabets
            for i, dup in enumerate(duplicates):
                child[child.index(dup)] = missing[i]
            population.append(child)
        
        #introduce random mutations to every key in the population
        for key in population:
            if random.random() <= mutationProb:
                i, j = random.sample(range(26), 2) #if there will be a mutation, swap two random keys
                key[i], key[j] = key[j], key[i]
        
        if noImproveCount > maxNoImprove:
            break
    
    return bestKey

#hill climb algorithm to try and find the best key by randomly swapping chars from a starting key
#in general, for the hillclimbing we want to reach many local maximums by climbing up hills using many different key
#starting points. Then we treat the best of the local maxima as the global best key
def hillclimb(cipher, startKey, maxIterations = 1000, maxNoImprove = 1000):
    """
    hyperparameters:
        maxIterations - number of hill climbing attempts, need a lot to avoid getting caught on one slope
        maxNoImprove - number of attempts to try and climb a slope before giving up
    """
    bestKey = None
    bestDecryption = None
    bestScore = float('-inf')

    #Continue interating until we hit max, or we can't find a better key
    for iteration in range(maxIterations):
        key = startKey[:]
        noImproveCount = 0
        #Prevents us from getting caught in a loop where we can't improve our current key
        while noImproveCount < maxNoImprove:   
            orginalDecryption = decrypt(cipher, key)
            originalScore = quadGramScore(orginalDecryption) #get current score with current key

            #swap two random chars in key and get score with that key
            c1, c2 = random.sample(range(26), 2)
            key[c1], key[c2] = key[c2], key[c1]
            newDecryption = decrypt(cipher, key)
            newScore = quadGramScore(newDecryption)

            #if score did not improve, swap back
            if originalScore >= newScore:
                key[c1], key[c2] = key[c2], key[c1]
                noImproveCount += 1
            else:
                #if the newScore is better than the old score, update all best values
                if newScore > bestScore:
                    bestKey, bestDecryption, bestScore, = key[:], newDecryption, newScore
                    print(f"Current best decryption is : {bestDecryption} with a score of {bestScore} using key {bestKey}")
            
    return bestDecryption #when hill climb is over, return the best decryption

#recursive function to segment a word into many splits, scoring each split in order to segment a decryption into words
def segmentWord(word, maxLength=20, cache={}):
    #base case where if there is no word, return empty list and score of 0
    if not word:
        return 0, []

    #use a cache to do top down memoization and save computing segments weve already done
    if word in cache:
        return cache[word]
    
    #find all possible splits in a word
    word = word.lower()
    splits = []
    for i in range(1, min(len(word), maxLength)):
        splits.append((word[:i], word[i:]))

    #recursive step where the function is called on the back end of the split and added to cumulative score
    allSegmentations = []
    for front, back in splits:
        # Avoid segmenting empty parts
        if not back:
            continue
        
        backScore, backSegmentation = segmentWord(back, maxLength, cache)       #segement the back end of the split
        totalScore = math.log10(singleWordFreqs(front)) + backScore             #add the best back segmentation split score
        allSegmentations.append((totalScore, [front] + backSegmentation))       #add to complete segements list
    
    #return the default if no segmentations are found
    if not allSegmentations:
        return 0, [word]

    #get the best segmentaion for this word and return it
    bestSegmentation = max(allSegmentations, key=lambda x: x[0])
    cache[word] = bestSegmentation
    return bestSegmentation

def main():
    #make sure input is valid
    solveNum = input("Which cipher do you want to solve? (1-4)\n")
    while str(solveNum) not in "1234":
        print('Invalid input')
        solveNum = input("Which cipher do you want to solve? (1-4)\n")
    solveNum = int(solveNum)

    startTime = time.time()
    #solve cipher 1 with caesars
    if solveNum == 1:
        decryptions = [caesars(ciphers[0], i) for i in range(1,26)]
        for decryption in decryptions:
            (prob, words) = segmentWord(decryption)
        prob, words = max(segmentWord(decryption) for decryption in decryptions) #split the decryption into the best fit words
        print("Cipher 1 decryption: ", ' '.join(words))
    
    #solve cipher 2-4 with genetic and hillclimb
    elif solveNum == 2:
        print('begin genetic search')
        bestKey = darwin(ciphers[1], maxIterations=1000, maxNoImprove=1000)
        print('begin hill climbing')
        decryption = hillclimb(decrypt(ciphers[1], bestKey), bestKey, maxIterations=1750, maxNoImprove=1750)
        print('begin word segmenting')
        prob, words = segmentWord(decryption)
        print("Cipher 2 decryption: ", ' '.join(words)) #should be around 5 minutes
    elif solveNum == 3:
        print('begin genetic search')
        bestKey = darwin(ciphers[2], maxIterations=500)
        print('begin hill climbing')
        decryption = hillclimb(decrypt(ciphers[2], bestKey), bestKey, maxIterations=750)
        print('begin word segmenting')
        prob, words = segmentWord(decryption)
        print("Cipher 3 decryption: ", ' '.join(words)) #should be around 2 minutes
    else:
        print('begin genetic search')
        bestKey = darwin(ciphers[3], maxIterations=1000, maxNoImprove=1000)
        print('begin hill climbing')
        decryption = hillclimb(decrypt(ciphers[3], bestKey), bestKey, maxIterations=2250, maxNoImprove=3250)
        print('begin word segmenting')
        prob, words = segmentWord(decryption)
        print("Cipher 4 decryption: ", ' '.join(words)) #should be around 4 minutes
        
    print(f"Total time: {time.time() - startTime} seconds") #print total time taken

main()
