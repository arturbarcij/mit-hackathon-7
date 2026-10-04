import { parseReferral } from "./parseReferral";
import { test, expect } from "vitest";
test("p",()=>{ const r=parseReferral("JANI1 M:OCC0412 P:P07 D:20261004 N:10 R:6 C:0 H:0 L:1 U:1 A:rust_high_pre_rains Q:87 X:ask");
expect(r?.counts.healthy).toBe(2); expect(r?.confidence).toBe(0.87); expect(parseReferral("hello")).toBeNull();});
