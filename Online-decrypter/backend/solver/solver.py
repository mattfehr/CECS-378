import math, random, time
from collections import Counter
from typing import Callable, List, Dict, Tuple, Optional

ALPHABET = list("abcdefghijklmnopqrstuvwxyz")

class GramDist(dict):
    def __init__(self, filename: str):
        super().__init__()
        self.gramCount = 0
        with open(filename, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                if "\t" in line:
                    word, count = line.split("\t")
                else:
                    # fallback for space-separated
                    parts = line.split()
                    if len(parts) != 2:
                        continue
                    word, count = parts
                self[word.lower()] = int(count)
                self.gramCount += self[word.lower()]

    def __call__(self, key: str) -> float:
        key = key.lower()
        if key in self:
            return float(self[key]) / self.gramCount
        # default tiny prob scaled by length
        return 1.0 / (self.gramCount * 10 ** max(0, len(key) - 2))


def load_quadgrams(path: str) -> Dict[str, float]:
    quadgramFreqs: Dict[str, float] = {}
    quadgramCount = 0
    with open(path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            gram, count = line.split()
            gram = gram.lower()
            c = int(count)
            quadgramFreqs[gram] = quadgramFreqs.get(gram, 0) + c
            quadgramCount += c
    for k, v in list(quadgramFreqs.items()):
        quadgramFreqs[k] = math.log10(v / quadgramCount)
    return quadgramFreqs


def preprocess(text: str) -> str:
    return "".join(ch for ch in text.lower() if ch.isalpha())


def caesars(string: str, offset: int) -> str:
    out = []
    for ch in string:
        if "a" <= ch <= "z":
            out.append(chr(ord('a') + (ord(ch) - ord('a') + offset) % 26))
        # ignore non-alpha (cipher is preprocessed)
    return "".join(out)


def decrypt(ciphertext: str, key: List[str]) -> str:
    sub = {shuffled: plain for plain, shuffled in zip(ALPHABET, key)}
    return "".join(sub.get(ch, ch) for ch in ciphertext)


def ngrams_list(msg: str, n: int) -> List[str]:
    return [msg[i:i+n] for i in range(0, len(msg) - n + 1)]


def quad_score(decryption: str, quadgramFreqs: Dict[str, float]) -> float:
    score = 0.0
    for q in ngrams_list(decryption, 4):
        score += quadgramFreqs.get(q, math.log10(0.01 / 4224127912))
    return score


def ngram_score(decryption: str, n: int, dist: GramDist) -> float:
    return sum(dist(g) for g in ngrams_list(decryption, n))


def total_score(decryption: str, bigrams: GramDist, trigrams: GramDist, quads: Dict[str, float]) -> float:
    return (
        ngram_score(decryption, 2, bigrams) * 1
        + ngram_score(decryption, 3, trigrams) * 2
        + quad_score(decryption, quads) * 4
    )


def permutation(alphabet: List[str]) -> List[str]:
    p = alphabet[:]
    random.shuffle(p)
    return p


def darwin(
    cipher: str,
    quadgrams: Dict[str, float],
    *,
    maxIterations=200,
    maxPopulation=100,
    survivePercent=0.67,
    maxNoImprove=20,
    mutationProb=0.1,
    seed: Optional[int] = None,
    progress: Optional[Callable[[str], None]] = None,
) -> List[str]:
    if seed is not None:
        random.seed(seed)
    population = [permutation(ALPHABET) for _ in range(maxPopulation)]
    bestScore, bestKey, noImprove = float('-inf'), None, 0

    for it in range(maxIterations):
        scores = [(quad_score(decrypt(cipher, k), quadgrams), k) for k in population]
        scores.sort(key=lambda x: x[0], reverse=True)
        survivors = [k for _, k in scores[: max(1, int(len(population) * survivePercent))]]
        topKey = survivors[0]
        topScore = quad_score(decrypt(cipher, topKey), quadgrams)
        if topScore > bestScore:
            bestScore, bestKey, noImprove = topScore, topKey[:], 0
            if progress:
                progress(f"[GA] iter={it} score={bestScore:.3f}")
        else:
            noImprove += 1
        population = survivors[:]
        while len(population) < maxPopulation:
            p1, p2 = random.sample(survivors, 2)
            child = [random.choice([p1[i], p2[i]]) for i in range(26)]
            missing = [l for l in ALPHABET if l not in set(child)]
            dupes = [l for l, c in Counter(child).items() if c > 1]
            for i, dup in enumerate(dupes):
                idx = child.index(dup)
                child[idx] = missing[i]
            population.append(child)
        for key in population:
            if random.random() <= mutationProb:
                i, j = random.sample(range(26), 2)
                key[i], key[j] = key[j], key[i]
        if noImprove > maxNoImprove:
            break
    assert bestKey is not None
    return bestKey


def hillclimb(
    cipher: str,
    startKey: List[str],
    quadgrams: Dict[str, float],
    *,
    maxIterations=1000,
    maxNoImprove=1000,
    seed: Optional[int] = None,
    progress: Optional[Callable[[str], None]] = None,
) -> Tuple[str, float, List[str]]:
    if seed is not None:
        random.seed(seed)
    bestKey: Optional[List[str]] = None
    bestDec: Optional[str] = None
    bestScore = float('-inf')

    for it in range(maxIterations):
        key = startKey[:]
        noImprove = 0
        while noImprove < maxNoImprove:
            dec0 = decrypt(cipher, key)
            s0 = quad_score(dec0, quadgrams)
            c1, c2 = random.sample(range(26), 2)
            key[c1], key[c2] = key[c2], key[c1]
            dec1 = decrypt(cipher, key)
            s1 = quad_score(dec1, quadgrams)
            if s1 <= s0:
                key[c1], key[c2] = key[c2], key[c1]
                noImprove += 1
            else:
                if s1 > bestScore:
                    bestKey, bestDec, bestScore = key[:], dec1, s1
                    if progress:
                        progress(f"[HC] score={bestScore:.3f} dec_preview={bestDec[:60]}")
        # restart with the same startKey (multi-start comes from GA diversity)
    assert bestDec is not None and bestKey is not None
    return bestDec, bestScore, bestKey


def segment_word(word: str, singleWordFreqs: GramDist, maxLength: int = 20) -> Tuple[float, list]:
    cache: Dict[str, Tuple[float, list]] = {}

    def _seg(w: str) -> Tuple[float, list]:
        if not w:
            return 0.0, []
        if w in cache:
            return cache[w]
        w = w.lower()
        allSeg = []
        for i in range(1, min(len(w), maxLength)):
            front, back = w[:i], w[i:]
            if not back:
                continue
            backScore, backSeg = _seg(back)
            totalScore = math.log10(singleWordFreqs(front)) + backScore
            allSeg.append((totalScore, [front] + backSeg))
        best = max(allSeg, key=lambda x: x[0]) if allSeg else (0.0, [w])
        cache[w] = best
        return best

    return _seg(word)


class Solver:
    def __init__(self, *, bigrams: str, trigrams: str, onegrams: str, quadgrams: str):
        self.bigramFreqs = GramDist(bigrams)
        self.trigramFreqs = GramDist(trigrams)
        self.singleWordFreqs = GramDist(onegrams)
        self.quadgramFreqs = load_quadgrams(quadgrams)

    def solve(self, raw_cipher: str, *, seed: Optional[int] = None, progress: Optional[Callable[[str], None]] = None) -> Dict:
        c = preprocess(raw_cipher)
        if progress:
            progress(f"[START] len={len(c)}")
        # quick Caesar scan (useful if the input was actually Caesar)
        best_caesar = max((caesars(c, i) for i in range(26)), key=lambda d: quad_score(d, self.quadgramFreqs))
        # GA to get a good start key, then HC to refine
        bestKey = darwin(c, self.quadgramFreqs, maxIterations=400, maxNoImprove=200, seed=seed, progress=progress)
        dec, score, key = hillclimb(c, bestKey, self.quadgramFreqs, maxIterations=1200, maxNoImprove=1200, seed=seed, progress=progress)
        # Word segmentation for readability
        prob, words = segment_word(dec, self.singleWordFreqs)
        return {
            "plaintext": " ".join(words),
            "raw_plaintext": dec,
            "score": score,
            "key": key,
            "caesar_guess": best_caesar,
        }