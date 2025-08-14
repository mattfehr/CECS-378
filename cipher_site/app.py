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
    _, words = user_solver.segmentWord(text)
    return " ".join(words), score, None  # No key for Caesar

def solve_substitution(ciphertext, time_limit=60, max_iter=800, max_no_improve=800):
    """
    Solve monoalphabetic substitution using user's GA + hillclimb,
    but stop after `time_limit` seconds and return the best found so far.
    """
    cipher = ''.join(ch.lower() for ch in ciphertext if ch.isalpha())
    start_time = time.time()

    # Darwin search for a good starting key with time check
    best_key = user_solver.darwin(
        cipher,
        maxIterations=max_iter,
        maxNoImprove=max_no_improve,
        time_limit=time_limit,
        start_time=start_time
    )

    # Hillclimb from that key with time check
    best_plain = user_solver.hillclimb(
        user_solver.decrypt(cipher, best_key),
        best_key,
        maxIterations=max_iter,
        maxNoImprove=max_no_improve,
        time_limit=time_limit,
        start_time=start_time
    )

    _, words = user_solver.segmentWord(best_plain)
    return " ".join(words), None, best_key  # No score, but return best key

@app.route('/', methods=['GET'])
def index():
    return render_template('index.html')

@app.route('/solve', methods=['POST'])
def solve():
    cipher = request.form.get('ciphertext', '').strip()
    method = request.form.get('method', 'substitution')
    time_limit = int(request.form.get('time_limit', 60))
    started = time.time()

    try:
        if method == 'caesar':
            plaintext, score, best_key = solve_caesar(cipher.replace(' ', '').lower())
            elapsed = time.time() - started
            return render_template(
                'result.html',
                plaintext=plaintext,
                elapsed=elapsed,
                method='Caesar (bruteforce)',
                score=score,
                ciphertext=cipher,
                best_key=best_key
            )
        else:
            plaintext, score, best_key = solve_substitution(cipher, time_limit=time_limit)

            elapsed = time.time() - started
            return render_template(
                'result.html',
                plaintext=plaintext,
                elapsed=elapsed,
                method=f'Monoalphabetic Substitution (GA + Hill Climb, {time_limit}s limit)',
                score=score,
                ciphertext=cipher,
                best_key=best_key
            )
    except Exception as e:
        return render_template(
            'result.html',
            plaintext=f'Error: {e}',
            elapsed=0.0,
            method=method,
            score=None,
            ciphertext=cipher,
            best_key=None
        )

if __name__ == "__main__":
    # For local dev: python app.py then open http://127.0.0.1:5000
    app.run(debug=True, host="0.0.0.0", port=5000)
