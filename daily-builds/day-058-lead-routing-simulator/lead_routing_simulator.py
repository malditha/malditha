#!/usr/bin/env python3
"""Simulate prioritized lead-routing rules without remote systems or value logging."""
import argparse,json
from pathlib import Path
MAX_BYTES=100_000;MAX_ROUTES=100;MAX_LEADS=1_000;OPS={"equals","one_of","exists"}
class InputError(ValueError):pass
def no_duplicates(pairs):
    out={}
    for key,value in pairs:
        if key in out:raise InputError(f"duplicate JSON key: {key}")
        out[key]=value
    return out
def load(path):
    if path.stat().st_size>MAX_BYTES:raise InputError("input exceeds 100 KB")
    try:return json.loads(path.read_text(encoding="utf-8"),object_pairs_hook=no_duplicates)
    except json.JSONDecodeError as exc:raise InputError(f"invalid JSON at line {exc.lineno}") from exc
def _keys(obj,allowed,where):
    extra=set(obj)-set(allowed)
    if extra:raise InputError(f"{where} has unsupported fields: {', '.join(sorted(extra))}")
def validate(data):
    if not isinstance(data,dict):raise InputError("root must be an object")
    _keys(data,{"routes","leads","default_team"},"root")
    routes=data.get("routes");leads=data.get("leads");default=data.get("default_team")
    if not isinstance(routes,list) or not routes or len(routes)>MAX_ROUTES:raise InputError("routes must contain 1 to 100 items")
    if not isinstance(leads,list) or len(leads)>MAX_LEADS:raise InputError("leads must contain 0 to 1000 items")
    if not isinstance(default,str) or not default.strip():raise InputError("default_team must be a non-empty string")
    names=set();ids=set()
    for i,route in enumerate(routes):
        if not isinstance(route,dict):raise InputError(f"route {i} must be an object")
        _keys(route,{"name","priority","team","all"},"route")
        name=route.get("name");priority=route.get("priority");team=route.get("team");conditions=route.get("all")
        if not isinstance(name,str) or not name.strip() or name in names:raise InputError("route names must be unique non-empty strings")
        names.add(name)
        if not isinstance(priority,int) or isinstance(priority,bool):raise InputError(f"route {name} priority must be an integer")
        if not isinstance(team,str) or not team.strip():raise InputError(f"route {name} team must be a non-empty string")
        if not isinstance(conditions,list) or not conditions:raise InputError(f"route {name} needs at least one condition")
        for condition in conditions:
            if not isinstance(condition,dict):raise InputError(f"route {name} condition must be an object")
            _keys(condition,{"field","op","value"},"condition")
            field=condition.get("field");op=condition.get("op")
            if not isinstance(field,str) or not field.strip() or op not in OPS:raise InputError(f"route {name} has an invalid condition")
            if op=="exists":
                if "value" in condition:raise InputError("exists does not accept value")
            elif "value" not in condition:raise InputError(f"{op} requires value")
            elif op=="one_of" and (not isinstance(condition["value"],list) or not condition["value"]):raise InputError("one_of value must be a non-empty list")
    for i,lead in enumerate(leads):
        if not isinstance(lead,dict):raise InputError(f"lead {i} must be an object")
        _keys(lead,{"id","attributes"},"lead")
        lead_id=lead.get("id");attrs=lead.get("attributes")
        if not isinstance(lead_id,str) or not lead_id.strip() or lead_id in ids:raise InputError("lead ids must be unique non-empty strings")
        ids.add(lead_id)
        if not isinstance(attrs,dict):raise InputError(f"lead {lead_id} attributes must be an object")
    return data
def condition_matches(attributes,condition):
    field=condition["field"];op=condition["op"]
    if op=="exists":return field in attributes and attributes[field] not in (None,"")
    if field not in attributes:return False
    if op=="equals":return attributes[field]==condition["value"]
    return attributes[field] in condition["value"]
def simulate(data):
    validate(data)
    ordered=sorted(enumerate(data["routes"]),key=lambda item:(-item[1]["priority"],item[0]))
    results=[];team_counts={}
    for lead in data["leads"]:
        matches=[route for _,route in ordered if all(condition_matches(lead["attributes"],c) for c in route["all"])]
        chosen=matches[0] if matches else None;team=chosen["team"] if chosen else data["default_team"]
        team_counts[team]=team_counts.get(team,0)+1
        results.append({"lead_id":lead["id"],"team":team,"route":chosen["name"] if chosen else None,"overlapping_routes":[r["name"] for r in matches[1:]]})
    return {"status":"review" if any(r["overlapping_routes"] for r in results) else "clear","summary":{"leads":len(results),"routes":len(data["routes"]),"teams":dict(sorted(team_counts.items()))},"results":results}
def format_text(report):
    lines=["Lead Routing Simulator",f"Status: {report['status'].upper()}",f"Leads: {report['summary']['leads']} · Routes: {report['summary']['routes']}","Assignments:"]
    for row in report["results"]:
        route=row["route"] or "default";overlap=f" · also matched: {', '.join(row['overlapping_routes'])}" if row["overlapping_routes"] else ""
        lines.append(f"- {row['lead_id']} -> {row['team']} ({route}){overlap}")
    if not report["results"]:lines.append("- none")
    return "\n".join(lines)
def main():
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument("input",type=Path);parser.add_argument("--json",action="store_true",dest="as_json");args=parser.parse_args()
    try:report=simulate(load(args.input))
    except (InputError,OSError) as exc:parser.exit(2,f"input error: {exc}\n")
    print(json.dumps(report,indent=2,sort_keys=True) if args.as_json else format_text(report));raise SystemExit(1 if report["status"]=="review" else 0)
if __name__=="__main__":main()
