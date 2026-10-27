# Day 058 — Lead Routing Simulator

Preview which team a sanitized lead would reach before translating routing rules into n8n.

## Purpose

The simulator applies prioritized equals, one_of, and exists conditions to local JSON. It reports the selected team, chosen route, and any lower-priority overlapping routes. Reports contain lead IDs and routing outcomes only; attribute values are never repeated.

It does not connect to n8n, contact a CRM, mutate leads, balance team capacity, or prove that a routing policy is fair or production-ready.

## Run

Requires Python 3.10+ and no third-party packages.

    python lead_routing_simulator.py sample.json
    python lead_routing_simulator.py sample.json --json
    python -m unittest -v test_lead_routing_simulator.py

Exit codes are 0 for a clear simulation, 1 when overlapping routes need review, and 2 for invalid input.

## Input

Each route has a unique name, integer priority, destination team, and an all list. Higher priority wins; source order breaks ties. A lead that matches nothing reaches default_team. Input is limited to 100 KB, 100 routes, and 1,000 leads.

## Skills practiced

- Deterministic priority ordering
- Declarative rule evaluation
- Overlap detection
- Defensive JSON validation
- Data-minimized reporting
- Standard-library tests

## Next improvement

Add an optional, explicit round-robin capacity model with a reproducible starting state.
