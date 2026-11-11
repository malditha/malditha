# Day 071 — Password Entropy Lens

Compare the theoretical search spaces of random password or passphrase generation recipes without typing a password. Python 3.10+, standard library only. No network, files written, password generation or secret input.

## Run

```sh
python lens.py --length 12 --pool 62 --compare-length 16
python lens.py --length 6 --pool 7776
python -m unittest -v
```

`length` is the number of independent draws, not necessarily characters. `pool` is the count of equally likely choices per draw. The second example models six words drawn uniformly with replacement from a 7,776-word list; it does not provide that list or generate words.

The model is **bits = length × log2(pool)**. Twelve uniform draws from 62 choices yield 71.45 bits; sixteen yield 95.267 bits. Output rounds to three decimals. Length is bounded to 1–1000 and pool to 2–1,000,000. Invalid input exits with status 2.

## Interpretation and limits

The calculation applies only to independent, uniformly random selection with replacement. It does not estimate the entropy of a human-chosen password, repeated pattern, biased generator or phrase. It does not account for reuse, leaks, phishing, storage or rate limiting, and makes no crack-time or safety claim. Never enter real credentials; this tool only accepts numeric recipe parameters.

## Skills practiced

Security model assumptions, logarithms, data minimization, CLI validation and unit/integration tests.

## Next improvement

Compare two different pool sizes while keeping the assumptions visible beside each result.
