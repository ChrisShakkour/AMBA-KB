# Usage: python check_arm_versions.py ihi0022 ihi0050 ...
# Lists all versions of each Arm document and the PDF link for the latest one
# (via the public documentation-service.arm.com metadata endpoint).
import json, sys, urllib.request
H={"User-Agent":"Mozilla/5.0"}
def get(u):
    try:
        return json.load(urllib.request.urlopen(urllib.request.Request(u,headers=H),timeout=30))
    except Exception as e:
        return {"_err":str(e)}
for doc in sys.argv[1:]:
    v=get(f"https://documentation-service.arm.com/documentation/{doc}/versions")
    if "_err" in v: print(doc,"ERR",v["_err"]); continue
    items=v if isinstance(v,list) else v.get("versions") or v.get("_embedded",{}).get("versions") or v
    vers=[]
    for it in (items if isinstance(items,list) else []):
        vers.append(it.get("version") or it.get("versionLabel"))
    print(f"== {doc}: versions {vers if vers else str(v)[:300]}")
    lat=get(f"https://documentation-service.arm.com/documentation/{doc}/latest")
    if "_err" in lat: print("  latest ERR",lat["_err"]); continue
    print("  title:",lat.get("title"),"| latest:",lat.get("versionLabel"),"| conf:",lat.get("metadata",{}).get("confidentiality"),"| published:",lat.get("metadata",{}).get("published","")[:10])
    for r in lat.get("_links",{}).get("resources",[]):
        print("  PDF:",r["name"],r["href"].split("?")[0])
