"""Render a static preview of the officer map from public/geo (for review, not shipped)."""
import json

import matplotlib
matplotlib.use("Agg")
import matplotlib.image as mpimg
import matplotlib.pyplot as plt
from matplotlib.patches import Patch, Polygon as MplPoly

import config as C

COL = {"outlier": "#b3261e", "unsure": "#e0a800", "normal": "#2f6f3e"}


def main():
    gj = json.loads((C.OUT / "plots.geojson").read_text())
    oj = json.loads((C.OUT / "outliers.json").read_text())
    (s, w), (n, e) = oj["overlay"]["bounds"]
    fig, ax = plt.subplots(figsize=(9, 9))
    ax.set_facecolor("#e9e6dc")
    ax.imshow(mpimg.imread(C.OUT / "ndvi_change.png"), extent=(w, e, s, n), zorder=1)
    for f in gj["features"]:
        p = f["properties"]
        ring = f["geometry"]["coordinates"][0]
        ax.add_patch(MplPoly(ring, closed=True, fill=p["status"] != "normal",
                             facecolor=COL[p["status"]] + "66", edgecolor=COL[p["status"]],
                             linewidth=1.8 if p["status"] != "normal" else 0.6, zorder=3))
        if p["status"] != "normal":
            cx = sum(x for x, _ in ring) / len(ring)
            cy = sum(y for _, y in ring) / len(ring)
            ax.annotate(p["plotId"], (cx, cy), xytext=(4, 4), textcoords="offset points", fontsize=6.5, zorder=4)
    ax.set_xlim(w, e); ax.set_ylim(s, n); ax.set_aspect(1 / 0.999)
    ax.set_title("Mathira West, Nyeri: synthetic plots on real Sentinel-2 NDVI change\n"
                 "(overlay: red = canopy loss vs prior dry seasons, green = gain)", fontsize=10)
    ax.legend(handles=[Patch(color=COL["outlier"], label=f"outlier ({oj['counts']['outlier']})"),
                       Patch(color=COL["unsure"], label=f"unsure ({oj['counts']['unsure']})"),
                       Patch(color=COL["normal"], label=f"normal ({oj['counts']['normal']})")], loc="lower left")
    fig.text(0.01, 0.01, "SYNTHETIC plots, members and deliveries. Real: Sentinel-2 NDVI (Copernicus, Earth Search), NASA POWER.",
             fontsize=7)
    out = C.ROOT.parent.parent / "kb" / "geo" / "preview.png"
    fig.savefig(out, dpi=110, bbox_inches="tight")
    print(out)


if __name__ == "__main__":
    main()
