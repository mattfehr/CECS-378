
# Substitution Cipher Decrypter (Flask)

A tiny web UI around your existing solver (`part1.py`).

## Run locally

```bash
python3 -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate
pip install -r requirements.txt
python app.py
# open http://127.0.0.1:5000
```

## Deploy (one easy option: Railway/Render/Fly.io)

- Build from this folder.
- Ensure a Python buildpack with `pip install -r requirements.txt` runs.
- Set the start command to `python app.py` (or use gunicorn in Procfile for production).

## Notes

- Caesar uses brute force with your `segmentWord` for scoring.
- Substitution uses `darwin` (genetic search) then `hillclimb` from your module. The runtime depends on cipher length.
- All n-gram files need to be present next to `app.py`:
  - `bigramFreq.txt`, `trigramFreq.txt`, `one-grams.txt`, `english_quadgrams.txt`.
