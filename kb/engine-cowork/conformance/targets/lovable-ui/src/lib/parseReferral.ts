// Parser for the JANI1 referral SMS format. Lives outside src/engine on purpose.
// Example: JANI1 M:OCC0412 P:P07 D:20261004 N:10 R:6 C:0 H:0 L:1 U:1 A:rust_high_pre_rains Q:87 X:ask
// Assumed field meaning: R rust, C cercospora, H phoma, L leaf miner, U not sure,
// healthy = N minus all others. Q is confidence in percent, X the farmer decision.

export interface ParsedReferral {
  member_id: string;
  plot_id: string;
  check_date: string;
  counts: Record<"healthy" | "rust" | "cercospora" | "phoma" | "miner" | "not_leaf", number>;
  uncertain: number;
  answer_id: string | null;
  confidence: number | null;
  decision: "act" | "wait" | "ask" | null;
}

export function parseReferral(input: string): ParsedReferral | null {
  const parts = input.trim().split(/\s+/);
  if (parts[0]?.toUpperCase() !== "JANI1") return null;
  const f: Partial<Record<string, string>> = {};
  for (const part of parts.slice(1)) {
    const i = part.indexOf(":");
    if (i < 1) continue;
    f[part.slice(0, i).toUpperCase()] = part.slice(i + 1);
  }
  const num = (k: string) => {
    const n = Number(f[k] ?? 0);
    return Number.isFinite(n) && n >= 0 ? Math.round(n) : NaN;
  };
  if (!/^[A-Z]{2,4}\d{2,6}$/i.test(f["M"] ?? "") || !/^P\d{1,3}$/i.test(f["P"] ?? "")) return null;
  const d = f["D"] ?? "";
  if (!/^\d{8}$/.test(d)) return null;
  const date = `${d.slice(0, 4)}-${d.slice(4, 6)}-${d.slice(6, 8)}`;
  if (Number.isNaN(Date.parse(date))) return null;
  const n = num("N"), r = num("R"), c = num("C"), h = num("H"), l = num("L"), u = num("U");
  if ([n, r, c, h, l, u].some(Number.isNaN) || n < 1 || n > 50) return null;
  const member = (f["M"] ?? "").toUpperCase();
  const plot = (f["P"] ?? "").toUpperCase();
  const healthy = n - r - c - h - l - u;
  if (healthy < 0) return null;
  const q = f["Q"] !== undefined ? Number(f["Q"]) : NaN;
  const x = (f["X"] ?? "").toLowerCase();
  return {
    member_id: member,
    plot_id: plot,
    check_date: date,
    counts: { healthy, rust: r, cercospora: c, phoma: h, miner: l, not_leaf: 0 },
    uncertain: u,
    answer_id: f["A"] ? f["A"].slice(0, 80) : null,
    confidence: Number.isFinite(q) && q >= 0 && q <= 100 ? q / 100 : null,
    decision: x === "act" || x === "wait" || x === "ask" ? x : null,
  };
}
