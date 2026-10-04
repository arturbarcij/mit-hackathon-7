Now build the cooperative officer dashboard at "/officer". Desktop and tablet first (the officer is online at the cooperative office), still usable at 360 px.

1. Enable Lovable Cloud. Tables:
   referrals(id uuid pk, created_at, member_id text, plot_id text, check_date date, counts jsonb, uncertain int, answer_id text, confidence numeric, decision text, photos_shared bool, photo_urls text[], status text default 'new', synthetic bool default false)
   corrections(id uuid pk, referral_id uuid fk, leaf_index int, model_label text, officer_label text, officer_id uuid, created_at)
   Simple email login for officers; RLS so only authenticated officers can read; anonymous users may only insert into referrals.
   Seed 15 referrals with synthetic = true.
2. OUTLIER MAP (centre of the page). Read static files `/geo/plots.geojson` and `/geo/outliers.json` (they will be added to public/geo via GitHub; until then create small placeholder versions in public/geo with 12 plots around lat -0.42, lon 36.95, every one marked synthetic). Leaflet with OpenStreetMap tiles. Colour each plot by outliers.plots[].reason: canopy_loss_check_leaves red, drop_other_cause_ask_officer amber, area_wide_weather blue, in_line_with_peers green, not_enough_data grey; also an icon or hatch pattern so it works without colour. Legend, and a fixed footer note: "Deliveries and plot shapes are synthetic. Satellite: Copernicus Sentinel-2. Rainfall: NASA POWER."
   Click a plot: side panel with member ID, "own change vs neighbours" bar (own_change_pct vs peer_change_pct), NDVI change, clear satellite observations, confidence ("Not sure" when low), the reason in plain words, and the button "Send leaf-check nudge" which shows the SMS text and opens the SMS app via an sms: link (label "simulated SMS gateway"; the officer presses send).
   Referrals appear as pins on their plot.
3. Referral queue beside the map, sorted by urgency (abstained or high incidence first). Detail view: counts, model labels per leaf, photos if shared, buttons Confirm / Correct label / Visit needed. Corrections save to the corrections table. "Export corrections (CSV)" labelled "new labelled examples for the next model".
4. "Paste SMS" box: paste a referral SMS in the JANI1 format (e.g. `JANI1 M:OCC0412 P:2 D:20261004 N:10 R:6 C:0 H:0 L:1 U:1 A:rust_high_pre_rains Q:87 X:ask`), parse it with parseReferral from src/engine (add a mock parser there only if missing), create a referral. Label "simulated SMS gateway".
Same design tokens as the farmer app. No charts beyond the bar, no KPIs, no marketing.
