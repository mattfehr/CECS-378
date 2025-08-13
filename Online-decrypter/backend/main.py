from fastapi import FastAPI, BackgroundTasks
from pydantic import BaseModel
from typing import Dict
from uuid import uuid4
import time

from solver.solver import Solver

DATA_DIR = "../data"
# Auto-pick quadgram file name (supports either english_quadgrams.txt or quadgramFreq.txt)
from pathlib import Path
quad_path = Path(f"{DATA_DIR}/english_quadgrams.txt")
if not quad_path.exists():
    alt = Path(f"{DATA_DIR}/quadgramFreq.txt")
    quad_path = alt if alt.exists() else quad_path

solver = Solver(
    bigrams=f"{DATA_DIR}/bigramFreq.txt",
    trigrams=f"{DATA_DIR}/trigramFreq.txt",
    onegrams=f"{DATA_DIR}/one-grams.txt",
    quadgrams=str(quad_path),
)

app = FastAPI(title="Cipher Solver API")

# in-memory task store {id: {status, result, logs}}
TASKS: Dict[str, Dict] = {}

class SolveRequest(BaseModel):
    cipher: str
    seed: int | None = None

@app.post("/solve")
async def create_task(req: SolveRequest, background: BackgroundTasks):
    task_id = str(uuid4())
    TASKS[task_id] = {"status": "running", "result": None, "logs": []}

    def progress(msg: str):
        TASKS[task_id]["logs"].append({"t": time.time(), "msg": msg})

    def run():
        try:
            res = solver.solve(req.cipher, seed=req.seed, progress=progress)
            TASKS[task_id]["status"] = "done"
            TASKS[task_id]["result"] = res
        except Exception as e:
            TASKS[task_id]["status"] = "error"
            TASKS[task_id]["result"] = {"error": str(e)}

    background.add_task(run)
    return {"task_id": task_id}

@app.get("/tasks/{task_id}")
async def get_task(task_id: str):
    task = TASKS.get(task_id)
    if not task:
        return {"error": "not_found"}
    return task