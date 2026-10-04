import { createFileRoute } from '@tanstack/react-router'
import { useState } from 'react'

export const Route = createFileRoute('/')({
  component: Home,
})

type Out = Record<string, unknown>

async function runOnce(): Promise<Out> {
  const t0 = performance.now()
  // onnxruntime-web is browser-only; import it lazily so the SSR bundle never touches it.
  const ort = await import('onnxruntime-web/wasm')
  // wasmPaths is left unset: the ort.wasm.bundle entry resolves the .wasm next to its own chunk
  // (Vite emits it as /assets/ort-wasm-simd-threaded-<hash>.wasm), which the precache glob covers.
  ort.env.wasm.numThreads = 1
  ort.env.wasm.proxy = false

  const [meta, modelBuf, mp3, answers] = await Promise.all([
    fetch('/model/model.json').then((r) => r.json()),
    fetch('/model/leaf.onnx').then((r) => r.arrayBuffer()),
    fetch('/audio/sw/test.mp3').then((r) => r.arrayBuffer()),
    fetch('/content/answers.json').then((r) => r.arrayBuffer()),
  ])
  const tFetched = performance.now()

  const session = await ort.InferenceSession.create(new Uint8Array(modelBuf), {
    executionProviders: ['wasm'],
    graphOptimizationLevel: 'all',
  })
  const tLoaded = performance.now()

  // Fixed deterministic input: 1x3x224x224, values from a simple LCG so every run is identical.
  const n = 3 * 224 * 224
  const data = new Float32Array(n)
  let s = 12345
  for (let i = 0; i < n; i++) {
    s = (s * 1103515245 + 12345) & 0x7fffffff
    data[i] = (s / 0x7fffffff) * 2 - 1
  }
  const input = new ort.Tensor('float32', data, [1, 3, 224, 224])

  // Warm-up run, then timed run.
  await session.run({ input })
  const tInfer0 = performance.now()
  const res = await session.run({ input })
  const tInfer1 = performance.now()
  const logits = res.logits.data as Float32Array
  let argmax = 0
  for (let i = 1; i < logits.length; i++) if (logits[i] > logits[argmax]) argmax = i

  return {
    ok: true,
    argmax,
    numClasses: logits.length,
    logits: Array.from(logits).map((v) => Number(v.toFixed(4))),
    modelVersion: meta.version,
    onnxBytes: modelBuf.byteLength,
    mp3Bytes: mp3.byteLength,
    answersBytes: answers.byteLength,
    fetchMs: Math.round(tFetched - t0),
    sessionCreateMs: Math.round(tLoaded - tFetched),
    inferMs: Math.round(tInfer1 - tInfer0),
    online: navigator.onLine,
    swControlled: !!navigator.serviceWorker?.controller,
  }
}

function Home() {
  const [out, setOut] = useState<string>('idle')
  const [busy, setBusy] = useState(false)
  return (
    <main className="mx-auto max-w-[360px] p-4 space-y-4">
      <h1 className="text-xl font-semibold">Jani PWA mirror</h1>
      <button
        id="run"
        disabled={busy}
        className="rounded bg-green-700 px-4 py-2 text-white disabled:opacity-50"
        onClick={async () => {
          setBusy(true)
          setOut('running')
          try {
            setOut(JSON.stringify(await runOnce(), null, 2))
          } catch (e) {
            setOut(JSON.stringify({ ok: false, error: String(e) }))
          } finally {
            setBusy(false)
          }
        }}
      >
        run
      </button>
      <pre id="out" className="whitespace-pre-wrap break-all text-xs">{out}</pre>
    </main>
  )
}
