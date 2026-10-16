"""Plan identical guest capacity on one host from explicit resource assumptions."""
import argparse
import json
import math
import sys


def calculate(cores, ram_gib, disk_gib, guest_vcpus, guest_ram_gib, guest_disk_gib,
              reserve_ram_gib=2, reserve_disk_gib=20, cpu_ratio=1):
    values = [cores, ram_gib, disk_gib, guest_vcpus, guest_ram_gib, guest_disk_gib,
              reserve_ram_gib, reserve_disk_gib, cpu_ratio]
    if any(isinstance(v, bool) or not isinstance(v, (int, float)) or not math.isfinite(v) for v in values):
        raise ValueError("all inputs must be finite numbers")
    if not isinstance(cores, int) or not isinstance(guest_vcpus, int) or not 1 <= cores <= 4096 or not 1 <= guest_vcpus <= 4096:
        raise ValueError("cores and guest vCPUs must be whole numbers from 1 to 4096")
    if any(not 0 < v <= 10000000 for v in [ram_gib, disk_gib, guest_ram_gib, guest_disk_gib]):
        raise ValueError("resource sizes must be positive and at most 10000000 GiB")
    if not 0 <= reserve_ram_gib <= ram_gib or not 0 <= reserve_disk_gib <= disk_gib:
        raise ValueError("reserves must fit within host RAM and storage")
    if not 1 <= cpu_ratio <= 16:
        raise ValueError("CPU allocation ratio must be from 1 to 16")
    budgets = {"cpu": cores * cpu_ratio, "ram": ram_gib - reserve_ram_gib,
               "disk": disk_gib - reserve_disk_gib}
    demands = {"cpu": guest_vcpus, "ram": guest_ram_gib, "disk": guest_disk_gib}
    limits = {key: math.floor(budgets[key] / demands[key]) for key in budgets}
    count = min(limits.values())
    return {"guest_count": count, "limits": limits,
            "limiting_resources": [key for key in limits if limits[key] == count],
            "remaining": {key: round(budgets[key] - count * demands[key], 3) for key in budgets},
            "budgets": budgets, "per_guest": demands,
            "units": {"cpu": "allocated vCPUs", "ram": "GiB", "disk": "GiB"},
            "assumptions": {"host_cores": cores, "cpu_ratio": cpu_ratio,
                            "reserve_ram_gib": reserve_ram_gib, "reserve_disk_gib": reserve_disk_gib},
            "scope": "Single-host allocation estimate for identical guests; not a performance, HA or storage-overhead guarantee."}


def main(argv=None):
    p = argparse.ArgumentParser(description=__doc__)
    for name in ["cores", "guest-vcpus"]:
        p.add_argument("--" + name, type=int, required=True)
    for name in ["ram-gib", "disk-gib", "guest-ram-gib", "guest-disk-gib"]:
        p.add_argument("--" + name, type=float, required=True)
    p.add_argument("--reserve-ram-gib", type=float, default=2)
    p.add_argument("--reserve-disk-gib", type=float, default=20)
    p.add_argument("--cpu-ratio", type=float, default=1)
    p.add_argument("--json", action="store_true")
    args = vars(p.parse_args(argv)); as_json = args.pop("json")
    try:
        result = calculate(**args)
    except ValueError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2
    if as_json:
        print(json.dumps(result, indent=2, allow_nan=False))
    else:
        print(f"Planned identical guests: {result['guest_count']}")
        print("Limiting resources: " + ", ".join(result["limiting_resources"]))
        for key, value in result["limits"].items():
            print(f"{key}: up to {value} guests; remaining {result['remaining'][key]} {result['units'][key]}")
        print(result["scope"])
    return 0 if result["guest_count"] else 1


if __name__ == "__main__": raise SystemExit(main())
