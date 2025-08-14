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

for i in range(len(ciphers)):
    ciphers[i] = ciphers[i].replace(" ", "").lower()

class GramDist(dict):
    def __init__(self, filename):
        self.gramCount = 0
        with open(filename) as file:
            for line in file:
                word, count = line.strip().split('\t')
                self[word] = int(count)
                self.gramCount += self[word]

    def __call__(self, key):
        if key in self:
            return float(self[key]) / self.gramCount
        else:
            return 1.0 / (self.gramCount * 10**(len(key)-2))

ALPHABET = list("abcdefghijklmnopqrstuvwxyz")
bigramFreqs = GramDist("bigramFreq.txt")
trigramFreqs = GramDist("trigramFreq.txt")
singleWordFreqs = GramDist("one-grams.txt")

quadgramFreqs = {}
quadgramCount = 0
for line in open("english_quadgrams.txt", "r"):
    gram, count = line.strip().split(' ')
    quadgramFreqs[gram.lower()] = int(count)
    quadgramCount += int(count)
for key in quadgramFreqs.keys():
    quadgramFreqs[key] = math.log10(quadgramFreqs[key] / quadgramCount)

def caesars(string, offset):
    text = []
    for char in string:
        text.append(chr(ord('a') + (ord(char) - ord('a') + offset) % 26))
    return "".join(text)

def decrypt(ciphertext, key):
    subDict = {shuffled_letter: letter for letter, shuffled_letter in zip(ALPHABET, key)}
    plaintext = []
    for char in ciphertext:
        if char.isalpha():
            plaintext.append(subDict[char.lower()])
        else:
            plaintext.append(char)
    return "".join(plaintext)

def nGramsList(msg, n):
    return [msg[i:i+n] for i in range(len(msg)-n+1)]

def quadGramScore(decryption):
    score = 0
    for quadGram in nGramsList(decryption, 4):
        if quadGram in quadgramFreqs:
            score += quadgramFreqs[quadGram]
        else:
            score += math.log10(.01 / 4224127912)
    return score

def nGramScore(decryption, n, nGramFreqs):
    return sum(nGramFreqs(gram) for gram in nGramsList(decryption, n))

def totalScore(decryption):
    score = 0
    score += nGramScore(decryption, 2, bigramFreqs) * 1
    score += nGramScore(decryption, 3, trigramFreqs) * 2
    score += quadGramScore(decryption) * 4
    return score

def permutation(alphabet):
    perm = alphabet[:]
    random.shuffle(perm)
    return perm

def darwin(cipher, maxIterations=200, maxPopulation=100, survivePercent=0.67,
           maxNoImprove=20, mutationProb=0.1, time_limit=None, start_time=None):
    bestScore, bestKey, noImproveCount = float('-inf'), None, 0
    population = [permutation(ALPHABET) for _ in range(maxPopulation)]

    for iteration in range(maxIterations):
        if time_limit and start_time and (time.time() - start_time > time_limit):
            break

        scores = [(quadGramScore(decrypt(cipher, key)), key) for key in population]
        scores.sort(reverse=True, key=lambda x: x[0])

        survivors = [scores[i][1] for i in range(max(1, math.floor(len(population)*survivePercent)))]

        topKey, topScore = survivors[0], quadGramScore(decrypt(cipher, survivors[0]))
        if topScore > bestScore:
            bestScore, bestKey, noImproveCount = topScore, topKey, 0
        else:
            noImproveCount += 1

        population = survivors[:]
        while len(population) < maxPopulation:
            p1, p2 = random.sample(survivors, 2)
            child = [random.choice([p1[i], p2[i]]) for i in range(26)]
            missing = [l for l in ALPHABET if l not in set(child)]
            duplicates = [l for l, c in Counter(child).items() if c > 1]
            for i, dup in enumerate(duplicates):
                child[child.index(dup)] = missing[i]
            population.append(child)

        for key in population:
            if random.random() <= mutationProb:
                i, j = random.sample(range(26), 2)
                key[i], key[j] = key[j], key[i]

        if noImproveCount > maxNoImprove:
            break

    return bestKey

def hillclimb(cipher, startKey, maxIterations=1000, maxNoImprove=1000, time_limit=None, start_time=None):
    bestKey = None
    bestDecryption = None
    bestScore = float('-inf')

    for iteration in range(maxIterations):
        if time_limit and start_time and (time.time() - start_time > time_limit):
            break

        key = startKey[:]
        noImproveCount = 0
        while noImproveCount < maxNoImprove:
            if time_limit and start_time and (time.time() - start_time > time_limit):
                break

            orginalDecryption = decrypt(cipher, key)
            originalScore = quadGramScore(orginalDecryption)

            c1, c2 = random.sample(range(26), 2)
            key[c1], key[c2] = key[c2], key[c1]
            newDecryption = decrypt(cipher, key)
            newScore = quadGramScore(newDecryption)

            if originalScore >= newScore:
                key[c1], key[c2] = key[c2], key[c1]
                noImproveCount += 1
            else:
                if newScore > bestScore:
                    bestKey, bestDecryption, bestScore = key[:], newDecryption, newScore

    return bestDecryption

def segmentWord(word, maxLength=20, cache={}):
    if not word:
        return 0, []
    if word in cache:
        return cache[word]

    word = word.lower()
    splits = [(word[:i], word[i:]) for i in range(1, min(len(word), maxLength))]
    allSegmentations = []
    for front, back in splits:
        if not back:
            continue
        backScore, backSegmentation = segmentWord(back, maxLength, cache)
        totalScore = math.log10(singleWordFreqs(front)) + backScore
        allSegmentations.append((totalScore, [front] + backSegmentation))
    if not allSegmentations:
        return 0, [word]
    bestSegmentation = max(allSegmentations, key=lambda x: x[0])
    cache[word] = bestSegmentation
    return bestSegmentation

def main():
    solveNum = input("Which cipher do you want to solve? (1-4)\n")
    while str(solveNum) not in "1234":
        print('Invalid input')
        solveNum = input("Which cipher do you want to solve? (1-4)\n")
    solveNum = int(solveNum)

    startTime = time.time()
    if solveNum == 1:
        decryptions = [caesars(ciphers[0], i) for i in range(1, 26)]
        prob, words = max(segmentWord(d) for d in decryptions)
        print("Cipher 1 decryption: ", ' '.join(words))
    elif solveNum == 2:
        bestKey = darwin(ciphers[1], maxIterations=1000, maxNoImprove=1000)
        decryption = hillclimb(decrypt(ciphers[1], bestKey), bestKey, maxIterations=1750, maxNoImprove=1750)
        prob, words = segmentWord(decryption)
        print("Cipher 2 decryption: ", ' '.join(words))
    elif solveNum == 3:
        bestKey = darwin(ciphers[2], maxIterations=500)
        decryption = hillclimb(decrypt(ciphers[2], bestKey), bestKey, maxIterations=750)
        prob, words = segmentWord(decryption)
        print("Cipher 3 decryption: ", ' '.join(words))
    else:
        bestKey = darwin(ciphers[3], maxIterations=1000, maxNoImprove=1000)
        decryption = hillclimb(decrypt(ciphers[3], bestKey), bestKey, maxIterations=2250, maxNoImprove=3250)
        prob, words = segmentWord(decryption)
        print("Cipher 4 decryption: ", ' '.join(words))

    print(f"Total time: {time.time() - startTime} seconds")

if __name__ == "__main__":
    main()
