import { useEffect, useState } from "react";

const API_BASE = "http://localhost:8000"; // change if deployed elsewhere

export default function App() {
  const [cipher, setCipher] = useState("");
  const [taskId, setTaskId] = useState(null);
  const [status, setStatus] = useState(null);
  const [logs, setLogs] = useState([]);
  const [result, setResult] = useState(null);
  const [seed, setSeed] = useState(42);

  const startSolve = async () => {
    setResult(null); setLogs([]); setStatus("running"); setTaskId(null);
    const r = await fetch(`${API_BASE}/solve`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ cipher, seed: Number(seed) || null }),
    }).then((r) => r.json());
    setTaskId(r.task_id);
  };

  useEffect(() => {
    if (!taskId) return;
    const iv = setInterval(async () => {
      const t = await fetch(`${API_BASE}/tasks/${taskId}`).then((r) => r.json());
      setStatus(t.status);
      setLogs(t.logs || []);
      setResult(t.result || null);
      if (t.status === "done" || t.status === "error") clearInterval(iv);
    }, 1000);
    return () => clearInterval(iv);
  }, [taskId]);

  return (
    <div className="min-h-screen bg-gray-50 text-gray-900 p-6">
      <div className="max-w-4xl mx-auto space-y-6">
        <header className="flex items-center justify-between">
          <h1 className="text-2xl font-bold">Substitution Cipher Solver</h1>
          <button
            onClick={() => {
              setCipher(""); setResult(null); setLogs([]); setStatus(null); setTaskId(null);
            }}
            className="px-3 py-2 rounded-xl bg-gray-200 hover:bg-gray-300"
          >Reset</button>
        </header>

        <div className="bg-white p-4 rounded-2xl shadow">
          <label className="block text-sm font-medium">Ciphertext</label>
          <textarea
            value={cipher}
            onChange={(e) => setCipher(e.target.value)}
            placeholder="Paste your cipher here..."
            className="mt-2 w-full h-40 p-3 border rounded-xl"
          />
          <div className="mt-3 flex gap-3 items-center">
            <label className="text-sm">Seed</label>
            <input
              type="number"
              value={seed}
              onChange={(e) => setSeed(e.target.value)}
              className="w-28 p-2 border rounded-xl"
            />
            <button
              onClick={startSolve}
              disabled={!cipher || status === "running"}
              className="px-4 py-2 rounded-2xl bg-black text-white disabled:opacity-50"
            >{status === "running" ? "Solving…" : "Solve"}</button>
          </div>
        </div>

        {logs.length > 0 && (
          <div className="bg-white p-4 rounded-2xl shadow">
            <h2 className="font-semibold mb-2">Progress</h2>
            <div className="h-40 overflow-auto text-sm font-mono whitespace-pre-wrap">
              {logs.map((l, i) => (
                <div key={i}>[{new Date(l.t * 1000).toLocaleTimeString()}] {l.msg}</div>
              ))}
            </div>
          </div>
        )}

        {result && (
          <div className="bg-white p-4 rounded-2xl shadow space-y-3">
            {result.error ? (
              <div className="text-red-600">Error: {result.error}</div>
            ) : (
              <>
                <div>
                  <h2 className="font-semibold">Plaintext (segmented)</h2>
                  <p className="mt-1 leading-relaxed">{result.plaintext}</p>
                </div>
                <div>
                  <h3 className="font-semibold">Raw plaintext</h3>
                  <p className="mt-1 break-all font-mono">{result.raw_plaintext}</p>
                </div>
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                  <div>
                    <h3 className="font-semibold">Score</h3>
                    <div className="mt-1">{result.score?.toFixed?.(3)}</div>
                  </div>
                  <div>
                    <h3 className="font-semibold">Key (substitution)</h3>
                    <div className="mt-1 font-mono break-all">{result.key?.join?.(" ")}</div>
                  </div>
                </div>
              </>
            )}
          </div>
        )}
      </div>
    </div>
  );
}