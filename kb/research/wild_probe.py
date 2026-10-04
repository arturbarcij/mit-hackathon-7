import json, urllib.request, urllib.parse, time
UA = {"User-Agent": "JaniResearch/1.0 (hackathon research; non-commercial test set)"}
def get(params):
    url = "https://api.inaturalist.org/v1/observations?" + urllib.parse.urlencode(params)
    j = json.load(urllib.request.urlopen(urllib.request.Request(url, headers=UA), timeout=60))
    time.sleep(1.1)
    return j["total_results"]
lic = "cc0,cc-by,cc-by-sa,cc-by-nc,cc-by-nc-sa"
for tid, nm in [(64342, "arabica"), (328339, "vastatrix"), (64343, "Coffea genus")]:
    print(nm, "all:", get({"taxon_id": tid, "per_page": 1}),
          "photos:", get({"taxon_id": tid, "photos": "true", "per_page": 1}),
          "research:", get({"taxon_id": tid, "quality_grade": "research", "per_page": 1}),
          "research+lic:", get({"taxon_id": tid, "quality_grade": "research", "photo_license": lic, "per_page": 1}),
          "any grade+lic:", get({"taxon_id": tid, "photo_license": lic, "per_page": 1}))
