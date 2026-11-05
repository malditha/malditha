#!/usr/bin/env python3
"""Generate a deterministic release checklist from a small deployment profile."""
from __future__ import annotations
import argparse, json, sys
from pathlib import Path

MAX_BYTES=128_000
ALLOWED_COMPONENTS={"application","database","infrastructure"}
ALLOWED_RISK={"low","medium","high"}

class InputError(ValueError): pass

BASE=[
 ("scope","Confirm the approved release scope","before"),
 ("tests","Record automated and manual test results","before"),
 ("artifact","Identify the exact build artifact or commit","before"),
 ("owner","Name the release owner and decision maker","before"),
 ("monitor","Confirm dashboards and alert ownership","after"),
 ("smoke","Run the agreed production smoke checks","after"),
]

def _task(task_id,label,phase,required=True):
    return {"id":task_id,"label":label,"phase":phase,"required":required}

def generate_checklist(profile: object) -> dict:
    if not isinstance(profile,dict): raise InputError("profile must be a JSON object")
    allowed={"release_id","components","risk","customer_facing"}
    if set(profile)-allowed: raise InputError("profile contains unknown fields")
    rid=profile.get("release_id")
    if not isinstance(rid,str) or not rid.strip() or len(rid)>80: raise InputError("release_id must be 1 to 80 characters")
    components=profile.get("components")
    if not isinstance(components,list) or not components or len(components)>3: raise InputError("components must be a non-empty array")
    if any(not isinstance(x,str) or x not in ALLOWED_COMPONENTS for x in components): raise InputError("component is not supported")
    if len(set(components))!=len(components): raise InputError("components must be unique")
    risk=profile.get("risk")
    if risk not in ALLOWED_RISK: raise InputError("risk must be low, medium or high")
    customer=profile.get("customer_facing")
    if not isinstance(customer,bool): raise InputError("customer_facing must be boolean")
    tasks=[_task(*row) for row in BASE]
    if "database" in components:
        tasks.extend([_task("backup","Verify a recent restorable database backup","before"),_task("migration","Dry-run the database migration and estimate duration","before"),_task("data-check","Validate critical data after migration","after")])
    if "infrastructure" in components:
        tasks.extend([_task("capacity","Review capacity and configuration impact","before"),_task("infra-health","Verify infrastructure health after the change","after")])
    if risk in {"medium","high"}:
        tasks.extend([_task("rollback","Write and review the rollback trigger and steps","before"),_task("watch","Assign a post-release observation window","after")])
    if risk=="high":
        tasks.extend([_task("approval","Record explicit go/no-go approval","before"),_task("rehearsal","Rehearse the release and rollback path","before")])
    if customer:
        tasks.extend([_task("message","Prepare customer-facing release communication","before"),_task("support","Brief support on expected behavior and escalation","before")])
    phase_order={"before":0,"after":1}
    tasks.sort(key=lambda x:(phase_order[x["phase"]],x["id"]))
    return {"release_id":rid,"profile":{"components":sorted(components),"risk":risk,"customer_facing":customer},"summary":{"tasks":len(tasks),"before":sum(t["phase"]=="before" for t in tasks),"after":sum(t["phase"]=="after" for t in tasks)},"tasks":tasks}

def _pairs(pairs):
    out={}
    for k,v in pairs:
        if k in out: raise InputError(f"duplicate JSON key: {k}")
        out[k]=v
    return out

def load(path: Path):
    if not path.is_file() or path.stat().st_size>MAX_BYTES: raise InputError("input must be a regular JSON file no larger than 128 KB")
    try: return json.loads(path.read_text(encoding="utf-8"),object_pairs_hook=_pairs)
    except (OSError,UnicodeError,json.JSONDecodeError) as exc: raise InputError("input must be valid UTF-8 JSON") from exc

def markdown(report: dict) -> str:
    lines=[f"# Release checklist: {report['release_id']}","",f"Risk: **{report['profile']['risk']}**  ","Components: "+", ".join(report["profile"]["components"]),""]
    for phase,title in (("before","Before release"),("after","After release")):
        lines.extend([f"## {title}",""])
        lines.extend(f"- [ ] {task['label']} (`{task['id']}`)" for task in report["tasks"] if task["phase"]==phase)
        lines.append("")
    return "\n".join(lines)

def main(argv=None):
    ap=argparse.ArgumentParser(description=__doc__);ap.add_argument("input",type=Path);ap.add_argument("--json",action="store_true");args=ap.parse_args(argv)
    try: report=generate_checklist(load(args.input))
    except InputError as exc: print(f"Input error: {exc}",file=sys.stderr);return 2
    print(json.dumps(report,indent=2) if args.json else markdown(report));return 0
if __name__=="__main__": raise SystemExit(main())
