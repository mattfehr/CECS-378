
import os
import time
from flask import Flask, render_template, request
import importlib.util
import sys

# Load user's solver module (part1.py) dynamically so we don't have to modify their file.
MODULE_PATH = os.path.join(os.path.dirname(__file__), 'part1.py')
spec = importlib.util.spec_from_file_location("user_solver", MODULE_PATH)
user_solver = importlib.util.module_from_spec(spec)
sys.modules["user_solver"] = user_solver
spec.loader.exec_module(user_solver)

app = Flask(__name__)

def solve_caesar(ciphertext):
    # Try all 25 shifts and score via user's word segmenter; return best
    decs = [user_solver.caesars(ciphertext, i) for i in range(1, 26)]
    best = max((user_solver.segmentWord(d)[0], d) for d in decs)
    score, text = best
    # Segment into words for readability
    _, words = user_solver.segmentWord(text)
    return " ".join(words), score

def solve_substitution(ciphertext, max_iter=800, max_no_improve=800):
    # Use genetic -> hillclimb on provided ciphertext (monoalphabetic substitution)
    # ciphertext should be lowercase letters with no spaces for the scoring routines
    cipher = ''.join(ch.lower() for ch in ciphertext if ch.isalpha())
    # Darwin search for a good starting key
    best_key = user_solver.darwin(cipher, maxIterations=max_iter, maxNoImprove=max_no_improve)
    # Hillclimb from that key
    best_plain = user_solver.hillclimb(user_solver.decrypt(cipher, best_key), best_key, maxIterations=max_iter, maxNoImprove=max_no_improve)
    # Segment for readability
    _, words = user_solver.segmentWord(best_plain)
    return " ".join(words)

@app.route('/', methods=['GET'])
def index():
    return render_template('index.html')

@app.route('/solve', methods=['POST'])
def solve():
    cipher = request.form.get('ciphertext', '').strip()
    method = request.form.get('method', 'substitution')
    started = time.time()
    try:
        if method == 'caesar':
            plaintext, score = solve_caesar(cipher.replace(' ', '').lower())
            elapsed = time.time() - started
            return render_template('result.html', plaintext=plaintext, elapsed=elapsed, method='Caesar (bruteforce)', score=score, ciphertext=cipher)
        else:
            plaintext = solve_substitution(cipher)
            elapsed = time.time() - started
            return render_template('result.html', plaintext=plaintext, elapsed=elapsed, method='Monoalphabetic Substitution (GA + Hill Climb)', score=None, ciphertext=cipher)
    except Exception as e:
        return render_template('result.html', plaintext=f'Error: {e}', elapsed=0.0, method=method, score=None, ciphertext=cipher)

if __name__ == "__main__":
    # For local dev: python app.py then open http://127.0.0.1:5000
    app.run(debug=True, host="0.0.0.0", port=5000)
