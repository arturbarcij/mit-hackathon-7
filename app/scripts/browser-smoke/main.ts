import { loadModel, classifyLeaf, sheetGate } from '../../src/engine/index.ts';
(window as any).engineReady = true;
(window as any).run = async (items: { name: string; b64: string; type: string }[]) => {
  const t0 = performance.now();
  const info = await loadModel();
  const tLoad = performance.now() - t0;
  const out: any[] = [];
  for (const it of items) {
    const bytes = Uint8Array.from(atob(it.b64), (c) => c.charCodeAt(0));
    const blob = new Blob([bytes], { type: it.type });
    const t1 = performance.now();
    const gated = await classifyLeaf(blob);
    const t2 = performance.now();
    const raw = await classifyLeaf(blob, { sheetGate: false });
    const t3 = performance.now();
    out.push({ name: it.name, gated: gated.label, reason: gated.quality.reason ?? null, sheet: gated.quality.sheet ?? null,
      label: raw.label, conf: +raw.confidence.toFixed(4), probs: raw.probs, blur: +raw.quality.blur.toFixed(1), bright: +raw.quality.brightness.toFixed(3), msGated: Math.round(t2 - t1), msRaw: Math.round(t3 - t2) });
  }
  return { info, tLoad: Math.round(tLoad), out, offscreen: typeof OffscreenCanvas !== 'undefined', ua: navigator.userAgent };
};
