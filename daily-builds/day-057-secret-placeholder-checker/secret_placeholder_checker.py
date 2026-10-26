#!/usr/bin/env python3
"""Find unresolved placeholder strings in a bounded local JSON document."""
from __future__ import annotations
import argparse, json, re
from pathlib import Path

MAX_BYTES=100_000; MAX_DEPTH=20; MAX_NODES=10_000
EXACT={"todo","tbd","changeme","change_me","replace_me","replace-this","insert_here","secret_here"}
TEMPLATE=re.compile(r"^(?:your|insert|replace)[_-][a-z0-9_-]+[_-]here$",re.I)
BRACKETED=re.compile(r"^(?:<[^<>]{1,80}>|\{\{[^{}]{1,80}\}\}|\$\{[^{}]{1,80}\})$")
KEY_HINT=re.compile(r"(?:secret|token|password|api[_-]?key|credential)",re.I)
class InputError(ValueError): pass
def pairs(items):
    out={}
    for k,v in items:
        if k in out: raise InputError("duplicate JSON key")
        out[k]=v
    return out
def load(path):
    if path.stat().st_size>MAX_BYTES: raise InputError("file exceeds 100 KB")
    try:return json.loads(path.read_text(encoding="utf-8"),object_pairs_hook=pairs)
    except (OSError,UnicodeError,json.JSONDecodeError) as e: raise InputError("could not read valid UTF-8 JSON") from e
def path_key(base,key):
    return f"{base}.{key}" if re.fullmatch(r"[A-Za-z_][A-Za-z0-9_]*",key) else f"{base}[{json.dumps(key)}]"
def classify(value,key=""):
    stripped=value.strip(); low=stripped.lower()
    if low in EXACT:return "known_placeholder"
    if TEMPLATE.fullmatch(stripped):return "template_placeholder"
    if BRACKETED.fullmatch(stripped) and KEY_HINT.search(key):return "credential_template"
    if not stripped and KEY_HINT.search(key):return "empty_credential_field"
    return None
def scan(document):
    findings=[]; visited=0
    def walk(value,path,key,depth):
        nonlocal visited
        visited+=1
        if visited>MAX_NODES:raise InputError("document exceeds 10,000 values")
        if depth>MAX_DEPTH:raise InputError("document exceeds depth 20")
        if isinstance(value,dict):
            for k,v in value.items():walk(v,path_key(path,k),k,depth+1)
        elif isinstance(value,list):
            for i,v in enumerate(value):walk(v,f"{path}[{i}]",key,depth+1)
        elif isinstance(value,str):
            code=classify(value,key)
            if code:findings.append({"path":path,"code":code})
    walk(document,"$","",0)
    findings.sort(key=lambda x:(x["path"],x["code"]))
    return {"status":"review" if findings else "clear","counts":{"values_checked":visited,"findings":len(findings)},"findings":findings}
def format_text(report):
    lines=["Secret Placeholder Checker",f"Status: {report['status'].upper()}",f"Values checked: {report['counts']['values_checked']}","Findings:"]
    lines+=([f"- {x['path']}: {x['code']}" for x in report["findings"]] or ["- none"])
    return "\n".join(lines)
def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument("document",type=Path);p.add_argument("--json",action="store_true");a=p.parse_args()
    try:r=scan(load(a.document))
    except (InputError,OSError) as e:p.exit(2,f"input error: {e}\n")
    print(json.dumps(r,indent=2) if a.json else format_text(r));return 1 if r["findings"] else 0
if __name__=="__main__":raise SystemExit(main())
