# Proxmox Capacity Calculator

Day 047 — Linux, DevOps & reliability.

## Purpose

Estimate how many identical guests fit on one host under explicit CPU, RAM and storage assumptions. Reports each resource limit, ties, available budgets and remaining capacity. This standalone planning tool does not connect to Proxmox.

## Run

Python 3.10+, no external dependencies:

```sh
python capacity.py --cores 8 --ram-gib 32 --disk-gib 500 --guest-vcpus 2 --guest-ram-gib 4 --guest-disk-gib 40
python capacity.py --cores 8 --ram-gib 32 --disk-gib 500 --guest-vcpus 2 --guest-ram-gib 4 --guest-disk-gib 40 --json
python -m unittest -v
```

Optional `--reserve-ram-gib` defaults to 2, `--reserve-disk-gib` to 20 and `--cpu-ratio` to 1. These are sample planning defaults, not Proxmox recommendations. Exit `0`: at least one guest fits; `1`: zero fit; `2`: invalid inputs.

## Model and boundaries

CPU budget = supplied core count × allocation ratio. RAM and storage budgets subtract their reserves. For each resource, floor(budget / per-guest allocation) gives its guest limit; the smallest limit is the answer. All storage and memory inputs use GiB. Supply usable storage capacity after any RAID or storage-layout decisions. Increasing CPU allocation ratio does not increase physical performance. Guest storage includes only the supplied allocation: snapshots, backups, thin provisioning, filesystem metadata and growth need separate allowances. CPU pinning, NUMA, I/O, network limits, mixed workloads, cluster placement and HA failover are outside this model. RAM is not overcommitted by the calculator. It reads no configuration and changes no infrastructure.

## Skills practiced

Capacity modeling, resource bottleneck analysis, reserve budgeting, finite-number validation, deterministic reports and standard-library tests.

## Next improvement

Add multiple guest profiles and an explicit placement model with separately documented assumptions.
