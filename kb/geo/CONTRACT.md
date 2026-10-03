# Geo outputs contract

Owner: geo. Consumers: ui (officer map), docs. Built by `app/geo/run.sh`. Static files, served from `app/public/geo/`, read only by the officer dashboard (online). Nothing here is farmer-facing.

Proposed for `kb/CONTRACTS.md` under "Geo outputs" (engine owns that file; see Requests in `kb/STATUS.md`).

## Files
| File | What | Size |
|---|---|---|
| `/geo/plots.geojson` | One polygon per member plot, WGS84 | about 60 KB |
| `/geo/outliers.json` | Model result per plot, context, legend, sources | about 50 KB |
| `/geo/ndvi_change.png` | Real NDVI change overlay, RGBA, WGS84 | about 210 KB |
| `/geo/visit_plan.json` | Ranked plots, tiers, one-day route for the officer | about 30 KB |
| `/geo/referrals_seed.json` | 18 synthetic leaf-check referrals for the dashboard seed | about 10 KB |

## `plots.geojson`
FeatureCollection, top-level `synthetic: true`, `season`. Each feature `properties`:
```ts
{
  plotId: string;          // "<memberId>-<plot>", e.g. "OCC0412-2"
  memberId: string;        // cooperative membership number, no names
  plot: number;
  areaHa: number;
  treesRegistered: number;
  deliveries: { season: string; kgCherry: number | null }[];  // coffee years "2022/23" .. "2025/26"
  synthetic: true;
  status: 'outlier' | 'unsure' | 'normal';   // for map colouring, same as outliers.json
  reason: string | null;   // first reason code, else first abstain code
  nextStep: NextStep;
  priorityPoints: number;   // from visit_plan.json
  tier: 'A' | 'B' | 'C';    // A visit now, B call or check records, C no action from this map
  hasReferral: boolean;     // a seed leaf-check referral exists for this plot
  ndviSeries: { season: string; median: number | null; clearPx: number; totalPx: number }[]; // real
}
```

## `outliers.json`
```ts
{
  version: 'geo-1'; generatedAt: string; season: '2025/26';
  area: { name: string; bbox: [number, number, number, number]; centre: [number, number] };
  synthetic: { plots: true; deliveries: true; members: true; ndvi: false; rainfall: false };
  method: { model: string; deliveryMetric: string; ndviMetric: string; thresholds: {...}; peerStats: {...} };
  context: {
    cooperativeMedianChangePct: number;  // median own-history change across members
    areaWideDrop: boolean;               // true when that median is -10% or worse
    rainfall: { shortRainsAnomalyPct: number; longRainsAnomalyPct: number; coffeeYearTotalMm: number; climatology: string; source: string };
    ndviSeasonMedians: Record<string, number>;
    ndviWindowRain: { window: string; rainMm: number; climatologyMm: number; z: number; caveat: string } | null;
    shortRains: { medianOnset: string; sdDays: number; shareOnsetBefore15Oct: number; onsetConfirmedThisYear: boolean; dataEnd: string; source: string } | null;
  };
  overlay: { image: '/geo/ndvi_change.png'; bounds: [[south, west], [north, east]]; meaning: string };
  counts: { outlier: number; unsure: number; normal: number };
  legend: Record<ReasonCode | AbstainCode, string>;   // officer-facing English labels
  nextSteps: Record<NextStep, string>;
  sources: { id: string; name: string; url: string; licence?: string; use: string }[];
  plots: PlotResult[];   // sorted: outlier, unsure, normal; then by score descending
}

type NextStep = 'visit' | 'call_member' | 'check_records' | 'ask_officer' | 'none';

interface PlotResult {
  plotId: string; memberId: string; plot: number;
  status: 'outlier' | 'unsure' | 'normal';
  confidence: 'high' | 'low';            // low exactly when status is 'unsure'
  reasons: ReasonCode[];
  abstainReasons: AbstainCode[];
  nextStep: NextStep;
  score: number | null;                  // max |z| of the two scores
  metrics: {
    kgCherry: number | null; kgPerTree: number | null; kgPerTreeBaseline: number | null;
    changePct: number | null; zDelivery: number | null; priorSeasons: number;
    ndvi: number | null; ndviBaseline: number | null; ndviChange: number | null; ndviLocalChange: number | null; zNdvi: number | null;
    clearPx: number; totalPx: number;
  };
  synthetic: true;
}
```

## Reason codes
| Code | Rule | Next step |
|---|---|---|
| `drop_with_canopy_loss` | delivery z at or below -3 and NDVI z at or below -2; or delivery z at or below -2 when NDVI z is at or below -3 (two signals corroborate) | `visit` |
| `drop_canopy_normal` | delivery z at or below -3 and NDVI z above -1.5. Could be side-selling, late picking or a record gap. The UI must not accuse. | `call_member` |
| `delivery_drop` | delivery z at or below -3, canopy not readable or unclear | (with abstain) `ask_officer` |
| `delivery_spike` | delivery z at or above +3 | `call_member` |
| `above_plausible_yield` | over 10 kg cherry per registered tree | `check_records` |
| `canopy_loss` | NDVI z at or below -3, deliveries not flagged. NDVI z is against the 12 nearest plots, so regional shifts cancel | `visit` |

## Abstain codes (status `unsure`, next step `ask_officer`)
| Code | Rule |
|---|---|
| `short_history` | fewer than 2 prior seasons of deliveries |
| `missing_delivery_record` | no delivery recorded this season |
| `plot_too_small` | under 0.10 ha (about 10 Sentinel-2 pixels) |
| `few_clear_pixels` | under 15 clear pixels or under 50% of the plot clear |
| `canopy_signal_unclear` | delivery drop, NDVI z between -2 and -1.5 |

A plot with good deliveries but no readable canopy is also `unsure`: we say the canopy was not checked rather than calling it normal.

## UI rules
- Show a visible "synthetic" tag on the map: plots, members and deliveries are made up.
- Show the source line for the NDVI overlay and rainfall (`sources` array).
- `unsure` is its own colour, never merged into `normal`.
- Never show `drop_canopy_normal` as wrongdoing. Use the legend text.

## `visit_plan.json`
```ts
{
  version: 'geo-1'; season: string; generatedAt: string;
  synthetic: { deliveries: true; referrals: true; plots: true; satellite: false };
  assumptions: { capacityPerVisitDay: number; circuity: number; office: { name; lon; lat }; weights: Record<string, number>; tiers: Record<'A'|'B'|'C', string>; note: string };
  tiers: { A: number; B: number; C: number };
  route: { stops: Stop[]; totalKm: number; randomOrderMeanKm: number; note: string };  // closed loop from the office, in visiting order
  ranking: RankedPlot[];        // every plot with points > 0, highest first
  referralsLinked: number; independentAgreement: number;   // plots with 2+ independent signals
}
interface Signal { source: 'satellite' | 'deliveries' | 'leaf_check' | 'records'; text: string }   // text is officer-facing English
interface Stop { stop: number; plotId; memberId; plot; lon; lat; legKm: number; points: number; independentSignals: number; tier: 'A'; signals: Signal[] }
interface RankedPlot { rank: number; plotId; memberId; plot; points: number; tier: 'A'|'B'|'C'; independentSignals: number; geoStatus: 'outlier'|'unsure'|'normal'; nextStep: NextStep; referralId: string | null; signals: Signal[] }
```
Points are a transparent sum, not a probability. Show `signals` as the reason for every ranked plot. Never show a plot as ranked without its reasons.

## `referrals_seed.json`
`{ synthetic: true, note, referrals: Referral[] }`. Each referral matches the `referrals` table in `kb/agents/ui.md` (`id, created_at, member_id, plot_id, check_date, counts, uncertain, answer_id, confidence, photos_shared, status, synthetic`) plus `sms` (a valid `JANI1` string, at most 160 GSM-7 characters, for the "paste SMS" box), `geoPlotId` (join key to `plots.geojson`), and `lon`, `lat` (plot centre for the map). Check dates fall on weekends, because the smartphone is home only at weekends. `answer_id` values mirror the example rule table in `kb/agents/content-voice.md`; they should be replaced with engine output when available.
