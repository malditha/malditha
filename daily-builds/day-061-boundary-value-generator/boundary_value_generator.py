#!/usr/bin/env python3
"""Generate deterministic boundary test cases from a small JSON field specification."""
from __future__ import annotations
import argparse, json, math, sys
from dataclasses import dataclass, asdict
from decimal import Decimal, InvalidOperation
from pathlib import Path
from typing import Any

MAX_FILE_BYTES=256_000
MAX_FIELDS=100
MAX_CASES=1000

class SpecError(ValueError): pass

def no_duplicates(pairs):
    out={}
    for key,value in pairs:
        if key in out: raise SpecError(f"duplicate JSON key: {key}")
        out[key]=value
    return out

def load_json(path: Path):
    if not path.is_file(): raise SpecError("input must be a readable file")
    if path.stat().st_size>MAX_FILE_BYTES: raise SpecError("input exceeds 256000 bytes")
    try: return json.loads(path.read_text(encoding="utf-8"), object_pairs_hook=no_duplicates)
    except UnicodeDecodeError as e: raise SpecError("input must be UTF-8") from e
    except json.JSONDecodeError as e: raise SpecError(f"invalid JSON: {e.msg}") from e

def dec(value, label):
    if isinstance(value,bool) or not isinstance(value,(int,float,str)): raise SpecError(f"{label} must be numeric")
    try: result=Decimal(str(value))
    except InvalidOperation as e: raise SpecError(f"{label} must be numeric") from e
    if not result.is_finite(): raise SpecError(f"{label} must be finite")
    return result

def output_number(value:Decimal, kind:str):
    if kind=="integer": return int(value)
    return float(value)

@dataclass(frozen=True)
class Case:
    field:str
    boundary:str
    relation:str
    value:Any
    expected_valid:bool

def validate(spec):
    if not isinstance(spec,dict) or set(spec)!={"fields"}: raise SpecError("top level must contain only fields")
    fields=spec["fields"]
    if not isinstance(fields,list) or not fields or len(fields)>MAX_FIELDS: raise SpecError("fields must contain 1 to 100 entries")
    names=set()
    for i,f in enumerate(fields):
        if not isinstance(f,dict): raise SpecError(f"field {i} must be an object")
        allowed={"name","type","minimum","maximum","step","min_length","max_length"}
        extra=set(f)-allowed
        if extra: raise SpecError(f"field {i} has unsupported keys: {', '.join(sorted(extra))}")
        name=f.get("name")
        if not isinstance(name,str) or not name.strip() or len(name)>80: raise SpecError(f"field {i} has invalid name")
        if name in names: raise SpecError(f"duplicate field name: {name}")
        names.add(name)
        kind=f.get("type")
        if kind not in {"integer","number","string"}: raise SpecError(f"{name}: type must be integer, number, or string")
        if kind=="string":
            if "minimum" in f or "maximum" in f or "step" in f: raise SpecError(f"{name}: numeric limits do not apply to strings")
            if not ({"min_length","max_length"}&set(f)): raise SpecError(f"{name}: add min_length or max_length")
            for key in ("min_length","max_length"):
                if key in f and (isinstance(f[key],bool) or not isinstance(f[key],int) or f[key]<0 or f[key]>10000): raise SpecError(f"{name}: {key} must be an integer from 0 to 10000")
            if f.get("min_length",0)>f.get("max_length",10000): raise SpecError(f"{name}: min_length cannot exceed max_length")
        else:
            if "min_length" in f or "max_length" in f: raise SpecError(f"{name}: length limits apply only to strings")
            if not ({"minimum","maximum"}&set(f)): raise SpecError(f"{name}: add minimum or maximum")
            step=dec(f.get("step",1),f"{name}.step")
            if step<=0: raise SpecError(f"{name}: step must be positive")
            if kind=="integer" and step!=step.to_integral_value(): raise SpecError(f"{name}: integer step must be a whole number")
            lo=dec(f["minimum"],f"{name}.minimum") if "minimum" in f else None
            hi=dec(f["maximum"],f"{name}.maximum") if "maximum" in f else None
            if kind=="integer" and any(x!=x.to_integral_value() for x in (lo,hi) if x is not None): raise SpecError(f"{name}: integer limits must be whole numbers")
            if lo is not None and hi is not None and lo>hi: raise SpecError(f"{name}: minimum cannot exceed maximum")
    return fields

def generate(spec):
    fields=validate(spec); cases=[]
    for f in fields:
        name,kind=f["name"],f["type"]
        if kind=="string":
            for key,label in (("min_length","minimum length"),("max_length","maximum length")):
                if key not in f: continue
                n=f[key]
                for relation,length,valid in (("below",n-1,False),("at",n,True),("above",n+1,key=="min_length")):
                    if length>=0: cases.append(Case(name,label,relation,"x"*length,valid))
        else:
            step=dec(f.get("step",1),f"{name}.step")
            for key,label in (("minimum","minimum"),("maximum","maximum")):
                if key not in f: continue
                n=dec(f[key],f"{name}.{key}")
                for relation,value,valid in (("below",n-step,key=="maximum"),("at",n,True),("above",n+step,key=="minimum")):
                    cases.append(Case(name,label,relation,output_number(value,kind),valid))
    if len(cases)>MAX_CASES: raise SpecError("generated case count exceeds 1000")
    return cases

def report(cases): return {"case_count":len(cases),"cases":[asdict(c) for c in cases]}

def main(argv=None):
    p=argparse.ArgumentParser(description=__doc__);p.add_argument("input",type=Path);p.add_argument("-o","--output",type=Path)
    args=p.parse_args(argv)
    try: result=json.dumps(report(generate(load_json(args.input))),indent=2,ensure_ascii=False)+"\n"
    except (OSError,SpecError) as e: print(f"error: {e}",file=sys.stderr);return 2
    if args.output: args.output.write_text(result,encoding="utf-8")
    else: print(result,end="")
    return 0
if __name__=="__main__": raise SystemExit(main())
