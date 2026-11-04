#!/usr/bin/env python3
"""Review user-facing error messages for clarity and recovery guidance."""
from __future__ import annotations
import argparse, json, re, sys
from pathlib import Path

MAX_BYTES, MAX_MESSAGES, MAX_TEXT = 256_000, 500, 500
GENERIC = {"error", "an error occurred", "something went wrong", "failed", "invalid"}
BLAME = re.compile(r"\b(you failed|your fault|you did not|you didn't|stupid|illegal)\b", re.I)
TECHNICAL = re.compile(r"\b(stack trace|exception|traceback|nullpointer|sqlstate|errno|undefined is not)\b", re.I)
ACTION = re.compile(r"\b(try|check|choose|enter|upload|refresh|contact|return|wait|use|remove|add|sign in|reload)\b", re.I)

class InputError(ValueError): pass

def review_message(item: dict) -> dict:
    if not isinstance(item, dict): raise InputError("each message must be an object")
    if set(item) - {"id", "text"}: raise InputError("message objects may only contain id and text")
    message_id, text = item.get("id"), item.get("text")
    if not isinstance(message_id, str) or not message_id.strip() or len(message_id) > 80:
        raise InputError("each id must be a non-empty string of at most 80 characters")
    if not isinstance(text, str): raise InputError(f"{message_id}: text must be a string")
    findings, stripped = [], text.strip()
    if not stripped:
        findings.append({"code":"empty","severity":"high","guidance":"Say what happened in plain language."})
    else:
        if len(stripped) > MAX_TEXT: findings.append({"code":"too_long","severity":"medium","guidance":"Keep the message under 500 characters and move diagnostics to logs."})
        if stripped.lower().rstrip(".!?") in GENERIC: findings.append({"code":"generic","severity":"high","guidance":"Name the failed task or input."})
        if TECHNICAL.search(stripped): findings.append({"code":"technical_detail","severity":"high","guidance":"Keep internal diagnostics in logs and show a safe explanation."})
        if BLAME.search(stripped): findings.append({"code":"blaming_tone","severity":"medium","guidance":"Describe the condition without blaming the person."})
        if not ACTION.search(stripped): findings.append({"code":"no_next_step","severity":"medium","guidance":"Add one realistic next step when recovery is possible."})
    return {"id":message_id,"status":"review" if findings else "ready","findings":findings}

def review_messages(data: object) -> dict:
    if not isinstance(data, list): raise InputError("input must be a JSON array")
    if not data or len(data) > MAX_MESSAGES: raise InputError("provide between 1 and 500 messages")
    results, seen = [], set()
    for item in data:
        result = review_message(item)
        if result["id"] in seen: raise InputError(f"duplicate id: {result['id']}")
        seen.add(result["id"]); results.append(result)
    return {"summary":{"ready":sum(r["status"]=="ready" for r in results),"review":sum(r["status"]=="review" for r in results)},"messages":results}

def _reject_duplicates(pairs):
    result={}
    for key,value in pairs:
        if key in result: raise InputError(f"duplicate JSON key: {key}")
        result[key]=value
    return result

def load_json(path: Path) -> object:
    if not path.is_file() or path.stat().st_size > MAX_BYTES: raise InputError("input must be a regular JSON file no larger than 256 KB")
    try: return json.loads(path.read_text(encoding="utf-8"), object_pairs_hook=_reject_duplicates)
    except (OSError, UnicodeError, json.JSONDecodeError) as exc: raise InputError("input must be valid UTF-8 JSON") from exc

def format_text(report: dict) -> str:
    lines=[f"Ready: {report['summary']['ready']} | Review: {report['summary']['review']}"]
    for item in report["messages"]:
        lines.append(f"\n[{item['status'].upper()}] {item['id']}")
        lines.extend(f"- {f['severity']}: {f['code']} — {f['guidance']}" for f in item["findings"])
    return "\n".join(lines)

def main(argv=None) -> int:
    parser=argparse.ArgumentParser(description=__doc__); parser.add_argument("input",type=Path); parser.add_argument("--json",action="store_true")
    args=parser.parse_args(argv)
    try: report=review_messages(load_json(args.input))
    except InputError as exc: print(f"Input error: {exc}",file=sys.stderr); return 2
    print(json.dumps(report,indent=2) if args.json else format_text(report))
    return 1 if report["summary"]["review"] else 0
if __name__=="__main__": raise SystemExit(main())
