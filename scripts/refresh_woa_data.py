
#!/usr/bin/env python3
import csv, io, json, os, sys, time, urllib.request, urllib.parse
from datetime import datetime, timezone
from pathlib import Path

PUB = "2PACX-1vR6W22ERb3UOEaYEoap6ykIoJXWfBOEfTLGh-mdJQ0uhfCYlrTj0MOKiN78rvs3avmT_IN7uTqVi2Iz"

SOURCES = {
    "members": 2078620130,
    "eventSetup": 363600942,
    "tinman": 722048278,
    "vaults": 897382777,
    "darkOmens": 1991117283,
    "trials": 23878375,
    "ragnarok": 247579126,
    "chestpoints": 1603255197,
    "eventExemptions": 1405131366,
    "growth": 213323401,
}

TOKENS = {
    "player","player name","official player name","player id","event id","event date",
    "current g-level","g-level","vault level","result / score","score","points","target",
    "current status","current might","might","week","reason"
}

def url_for(gid):
    return f"https://docs.google.com/spreadsheets/d/e/{PUB}/pub?gid={gid}&single=true&output=csv"

def download(url, tries=6):
    last = None
    for attempt in range(tries):
        try:
            req = urllib.request.Request(
                url + "&cacheBust=" + str(int(time.time()*1000)),
                headers={"User-Agent": "Mozilla/5.0 WoA-Data-Refresh/1.0"}
            )
            with urllib.request.urlopen(req, timeout=30) as r:
                body = r.read().decode("utf-8-sig")
            if body.lstrip().startswith("<"):
                raise RuntimeError("HTML response received instead of CSV")
            if len(body.strip()) < 10:
                raise RuntimeError("Empty CSV response")
            return body
        except Exception as e:
            last = e
            if attempt < tries-1:
                time.sleep(min(2**attempt, 15))
    raise RuntimeError(f"Source failed after {tries} attempts: {last}")

def header_score(row):
    vals = {str(x).strip().lower() for x in row}
    return sum(1 for t in TOKENS if t in vals)

def rows_to_objects(csv_text, name):
    matrix = list(csv.reader(io.StringIO(csv_text)))
    if not matrix:
        raise RuntimeError(f"{name}: empty CSV")

    best = max(range(min(60, len(matrix))), key=lambda i: header_score(matrix[i]))
    headers = [(x.strip() if x.strip() else f"Column{j+1}") for j,x in enumerate(matrix[best])]

    # Growth must have Week / Player / Might.
    if name == "growth":
        lower = [h.lower() for h in headers]
        if not all(x in lower for x in ["week","player","might"]):
            for i,row in enumerate(matrix[:60]):
                lr = [str(x).strip().lower() for x in row]
                if all(x in lr for x in ["week","player","might"]):
                    best = i
                    headers = [(x.strip() if x.strip() else f"Column{j+1}") for j,x in enumerate(matrix[best])]
                    break

    out = []
    for row in matrix[best+1:]:
        obj = {}
        meaningful = False
        for j,h in enumerate(headers):
            v = row[j].strip() if j < len(row) else ""
            obj[h] = v
            if v:
                meaningful = True
        if meaningful:
            out.append(obj)

    # All operational sources must have rows. Exemptions may legitimately be empty.
    if name != "eventExemptions" and not out:
        raise RuntimeError(f"{name}: no usable rows after parsing")
    return out

def main():
    payload = {}
    for name,gid in SOURCES.items():
        print(f"Fetching {name}...")
        payload[name] = rows_to_objects(download(url_for(gid)), name)
        print(f"  {len(payload[name])} rows")

    # All-or-nothing: only write after every source succeeded.
    payload["_meta"] = {
        "source": "Google Sheets published CSVs via GitHub Actions",
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "status": "complete",
    }

    target = Path("data.json")
    tmp = Path("data.json.tmp")
    tmp.write_text(json.dumps(payload, ensure_ascii=False, separators=(",", ":")), encoding="utf-8")

    # Validate the serialized file before replacing last known good snapshot.
    check = json.loads(tmp.read_text(encoding="utf-8"))
    missing = [k for k in SOURCES if k not in check or not isinstance(check[k], list)]
    if missing:
        tmp.unlink(missing_ok=True)
        raise RuntimeError("Validation failed: " + ", ".join(missing))

    tmp.replace(target)
    print("Complete data.json written successfully.")

if __name__ == "__main__":
    main()
