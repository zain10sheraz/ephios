"""Fail (exit 1) if the Cosmic Ray kill rate is below the threshold.

Usage: cosmic-ray dump session.sqlite | python scripts/check_mutation_score.py --min 90
Kill rate = killed / (killed + survived + timeout); 'incompetent' mutants (invalid code) are excluded.
"""

import argparse
import collections
import json
import sys

parser = argparse.ArgumentParser()
parser.add_argument("--min", type=float, required=True)
args = parser.parse_args()

counts = collections.Counter()
for line in sys.stdin:
    work, result = json.loads(line)
    if result:
        counts[result["test_outcome"]] += 1

valid = counts["killed"] + counts["survived"] + counts["timeout"]
if valid == 0:
    sys.exit("no completed mutants found - refusing to pass")
rate = 100.0 * counts["killed"] / valid
print(f"mutants: {dict(counts)}  kill rate = {rate:.2f}% (threshold {args.min}%)")
sys.exit(0 if rate >= args.min else 1)
