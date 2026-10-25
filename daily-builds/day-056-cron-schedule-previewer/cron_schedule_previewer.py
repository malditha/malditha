#!/usr/bin/env python3
"""Preview upcoming times for a bounded five-field cron expression."""
from __future__ import annotations
import argparse, json
from datetime import datetime, timedelta, timezone
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

LIMITS=[(0,59),(0,23),(1,31),(1,12),(0,6)]

class CronError(ValueError): pass

def parse_field(text, low, high):
    values=set()
    for part in text.split(","):
        if not part: raise CronError("empty cron list item")
        base, slash, step_text=part.partition("/")
        step=int(step_text) if slash and step_text.isdigit() else 1
        if slash and (not step_text.isdigit() or step<1): raise CronError("step must be a positive integer")
        if base=="*": start,end=low,high
        elif "-" in base:
            a,b=base.split("-",1)
            if not (a.isdigit() and b.isdigit()): raise CronError("range bounds must be integers")
            start,end=int(a),int(b)
        elif base.isdigit(): start=end=int(base)
        else: raise CronError("unsupported cron token")
        if start<low or end>high or start>end: raise CronError("cron value is outside its field range")
        values.update(range(start,end+1,step))
    return values

def parse_expression(expression):
    fields=expression.split()
    if len(fields)!=5: raise CronError("expected five cron fields")
    return [parse_field(text,*bounds) for text,bounds in zip(fields,LIMITS)]

def matches(local, parsed, expression):
    minute,hour,dom,month,dow=parsed
    cron_dow=(local.weekday()+1)%7
    if local.minute not in minute or local.hour not in hour or local.month not in month: return False
    raw=expression.split()
    dom_match=local.day in dom; dow_match=cron_dow in dow
    if raw[2]=="*" and raw[4]=="*": return True
    if raw[2]=="*": return dow_match
    if raw[4]=="*": return dom_match
    return dom_match or dow_match

def preview(expression, zone_name, start, count=5):
    if not 1<=count<=20: raise CronError("count must be between 1 and 20")
    parsed=parse_expression(expression)
    try: zone=ZoneInfo(zone_name)
    except ZoneInfoNotFoundError as exc: raise CronError("unknown IANA time zone") from exc
    cursor=start.astimezone(timezone.utc).replace(second=0,microsecond=0)+timedelta(minutes=1)
    found=[]
    deadline=cursor+timedelta(days=366*5)
    while cursor<=deadline and len(found)<count:
        local=cursor.astimezone(zone)
        if matches(local,parsed,expression):
            found.append({"local":local.isoformat(),"utc":cursor.isoformat()})
        cursor+=timedelta(minutes=1)
    if len(found)<count: raise CronError("could not find enough runs within five years")
    return {"expression":expression,"timezone":zone_name,"starts_after":start.isoformat(),"runs":found}

def parse_start(text):
    try: value=datetime.fromisoformat(text.replace("Z","+00:00"))
    except ValueError as exc: raise CronError("start must be an ISO 8601 timestamp") from exc
    if value.tzinfo is None: raise CronError("start timestamp must include an offset")
    return value

def format_text(report):
    lines=[f"Cron Schedule Preview: {report['expression']}",f"Timezone: {report['timezone']}",""]
    lines += [f"{i}. {run['local']}  |  {run['utc']}" for i,run in enumerate(report["runs"],1)]
    return "\n".join(lines)

def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("expression"); p.add_argument("--timezone",default="UTC")
    p.add_argument("--start",required=True); p.add_argument("--count",type=int,default=5); p.add_argument("--json",action="store_true")
    a=p.parse_args()
    try: report=preview(a.expression,a.timezone,parse_start(a.start),a.count)
    except CronError as exc: p.exit(2,f"input error: {exc}\n")
    print(json.dumps(report,indent=2) if a.json else format_text(report)); return 0
if __name__=="__main__": raise SystemExit(main())
