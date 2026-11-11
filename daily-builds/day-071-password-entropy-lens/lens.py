"""Compare uniform random password-generation spaces without collecting secrets."""
import argparse
import json
import math


def estimate(length, pool):
    """Entropy assumes independent uniform draws, with replacement."""
    if type(length) is not int or not 1 <= length <= 1000:
        raise ValueError('length must be an integer from 1 to 1000')
    if type(pool) is not int or not 2 <= pool <= 1000000:
        raise ValueError('pool must be an integer from 2 to 1000000')
    return {'length': length, 'pool': pool, 'bits': round(length * math.log2(pool), 3)}


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--length', type=int, required=True, help='Number of independent random draws')
    p.add_argument('--pool', type=int, required=True, help='Number of equally likely choices per draw')
    p.add_argument('--compare-length', type=int)
    a = p.parse_args()
    try:
        result = {'model': 'Independent uniform draws with replacement; not a password strength score',
                  'baseline': estimate(a.length, a.pool)}
        if a.compare_length is not None:
            result['comparison'] = estimate(a.compare_length, a.pool)
            result['additional_bits'] = round((a.compare_length-a.length)*math.log2(a.pool),3)
        print(json.dumps(result, indent=2))
    except ValueError as e:
        p.error(str(e))


if __name__ == '__main__':
    main()
