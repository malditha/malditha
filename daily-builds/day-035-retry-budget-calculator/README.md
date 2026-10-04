# Retry Budget Calculator

A dependency-free Python CLI that calculates how many retry delays fit inside a fixed wait budget. It models capped exponential backoff and can reserve a conservative allowance for jitter without making network requests.

## Run

```bash
python retry_budget_calculator.py \
  --budget-ms 12000 \
  --initial-delay-ms 500 \
  --multiplier 2 \
  --max-delay-ms 4000 \
  --jitter-percent 20 \
  --max-retries 8
```

Add `--json` for machine-readable output.

## Test

```bash
python -m unittest -v
```

## What it reports

- retry delays that fit the total wait budget
- retries allowed versus total attempts
- wait used and remaining
- the next delay that would exceed the budget
- whether every requested retry fits

The budget covers waiting only. Request execution time and network latency are deliberately excluded, and the result does not guarantee a successful operation.

## Skills practiced

- API retry and backoff reasoning
- precise decimal arithmetic and conservative rounding
- defensive CLI validation
- human-readable and JSON output
- deterministic unit testing

## Next improvement

Accept a separate per-attempt timeout and show a combined end-to-end time envelope.
